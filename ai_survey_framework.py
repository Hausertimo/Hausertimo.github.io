"""
AI-Powered Conversational Survey Framework

A standalone framework for creating engaging, AI-driven surveys with dynamic questioning,
answer validation, conditional branching, and intelligent follow-ups.

ARCHITECTURE:
- SurveyQuestion: Defines individual questions with AI validation and conditional logic
- Survey: Collection of questions with flow control
- SurveySession: Manages user progress through a survey
- SurveyManager: Handles survey lifecycle and storage
- Blueprint: Flask API endpoints for survey interaction

USAGE EXAMPLE:

    # 1. Define your survey
    from ai_survey_framework import Survey, SurveyQuestion, survey_manager, survey_bp

    my_survey = Survey(
        survey_id="customer_satisfaction",
        title="Customer Satisfaction Survey",
        description="Help us understand your experience"
    )

    # 2. Add questions
    my_survey.add_question(SurveyQuestion(
        question_id="q1",
        text="What product did you purchase?",
        question_type="text",
        ai_validate=True,  # AI validates the answer
        required=True
    ))

    my_survey.add_question(SurveyQuestion(
        question_id="q2",
        text="How satisfied are you with {q1}?",  # References previous answer
        question_type="rating",
        options=["Very Unsatisfied", "Unsatisfied", "Neutral", "Satisfied", "Very Satisfied"],
        required=True
    ))

    my_survey.add_question(SurveyQuestion(
        question_id="q3_negative",
        text="We're sorry to hear that. What could we improve?",
        question_type="text",
        condition=lambda answers: answers.get("q2") in ["Very Unsatisfied", "Unsatisfied"],
        ai_followup=True  # AI generates personalized follow-up
    ))

    # 3. Register the survey
    survey_manager.register_survey(my_survey)

    # 4. Register blueprint in your app.py
    app.register_blueprint(survey_bp, url_prefix='/api/survey')

    # 5. Initialize dependencies
    from ai_survey_framework import init_dependencies
    init_dependencies(redis_client)

API ENDPOINTS:
    POST /api/survey/start
        Body: {"survey_id": "customer_satisfaction", "metadata": {...}}
        Returns: {"session_id": "...", "first_question": {...}}

    POST /api/survey/answer
        Body: {"session_id": "...", "question_id": "...", "answer": "..."}
        Returns: {"next_question": {...}, "progress": 60, "complete": false}

    GET /api/survey/status/<session_id>
        Returns: {"progress": 60, "current_question": {...}, "complete": false}

    GET /api/survey/results/<session_id>
        Returns: {"answers": {...}, "metadata": {...}, "completed_at": "..."}

    GET /api/survey/export/<session_id>
        Returns: JSON export of full survey session

FEATURES:
    ✓ AI-powered answer validation
    ✓ Dynamic question generation based on previous answers
    ✓ Conditional branching (skip/show questions based on logic)
    ✓ Template substitution ({q1} replaced with answer to q1)
    ✓ Progress tracking
    ✓ Session persistence in Redis
    ✓ Multiple question types (text, rating, multiple_choice, yes_no)
    ✓ AI-generated follow-up questions
    ✓ Export results to JSON
    ✓ Standalone - doesn't modify other code
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Any
from flask import Blueprint, request, jsonify, session
from functools import wraps

# Initialize logger
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL DEPENDENCIES (injected from app.py)
# ============================================================================

redis_client = None

def init_dependencies(redis_conn):
    """
    Initialize framework dependencies.
    Call this from app.py after creating Redis client.

    Args:
        redis_conn: Redis client instance
    """
    global redis_client
    redis_client = redis_conn
    logger.info("AI Survey Framework dependencies initialized")


# ============================================================================
# CORE CLASSES
# ============================================================================

class SurveyQuestion:
    """
    Represents a single survey question with validation and conditional logic.

    Attributes:
        question_id (str): Unique identifier for the question
        text (str): Question text (supports {q_id} template substitution)
        question_type (str): Type of question (text, rating, multiple_choice, yes_no)
        options (list): For multiple_choice or rating, list of options
        required (bool): Whether answer is required
        ai_validate (bool): Use AI to validate answer quality
        ai_followup (bool): Generate AI follow-up based on answer
        condition (callable): Function that determines if question should be shown
        validation_prompt (str): Custom prompt for AI validation
        metadata (dict): Additional metadata for the question
    """

    def __init__(
        self,
        question_id: str,
        text: str,
        question_type: str = "text",
        options: Optional[List[str]] = None,
        required: bool = True,
        ai_validate: bool = False,
        ai_followup: bool = False,
        condition: Optional[Callable[[Dict], bool]] = None,
        validation_prompt: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.question_id = question_id
        self.text = text
        self.question_type = question_type
        self.options = options or []
        self.required = required
        self.ai_validate = ai_validate
        self.ai_followup = ai_followup
        self.condition = condition
        self.validation_prompt = validation_prompt
        self.metadata = metadata or {}

    def should_show(self, answers: Dict[str, Any]) -> bool:
        """
        Determine if this question should be shown based on previous answers.

        Args:
            answers: Dictionary of previous answers

        Returns:
            True if question should be shown, False otherwise
        """
        if self.condition is None:
            return True
        try:
            return self.condition(answers)
        except Exception as e:
            logger.error(f"Error evaluating condition for question {self.question_id}: {e}")
            return True

    def render_text(self, answers: Dict[str, Any]) -> str:
        """
        Render question text with template substitution.

        Example: "How satisfied are you with {q1}?" -> "How satisfied are you with iPhone?"

        Args:
            answers: Dictionary of previous answers

        Returns:
            Rendered question text
        """
        text = self.text
        for q_id, answer in answers.items():
            placeholder = f"{{{q_id}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(answer))
        return text

    def to_dict(self, answers: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Convert question to dictionary for API responses.

        Args:
            answers: Previous answers for template rendering

        Returns:
            Dictionary representation of question
        """
        answers = answers or {}
        return {
            "question_id": self.question_id,
            "text": self.render_text(answers),
            "type": self.question_type,
            "options": self.options,
            "required": self.required,
            "metadata": self.metadata
        }


class Survey:
    """
    Represents a complete survey with multiple questions and flow logic.

    Attributes:
        survey_id (str): Unique identifier for the survey
        title (str): Survey title
        description (str): Survey description
        questions (list): List of SurveyQuestion objects
        metadata (dict): Additional survey metadata
    """

    def __init__(
        self,
        survey_id: str,
        title: str,
        description: str = "",
        metadata: Optional[Dict] = None
    ):
        self.survey_id = survey_id
        self.title = title
        self.description = description
        self.questions: List[SurveyQuestion] = []
        self.metadata = metadata or {}

    def add_question(self, question: SurveyQuestion):
        """Add a question to the survey."""
        self.questions.append(question)
        logger.info(f"Added question {question.question_id} to survey {self.survey_id}")

    def get_question(self, question_id: str) -> Optional[SurveyQuestion]:
        """Get a question by ID."""
        for q in self.questions:
            if q.question_id == question_id:
                return q
        return None

    def get_next_question(self, answers: Dict[str, Any]) -> Optional[SurveyQuestion]:
        """
        Get the next unanswered question based on conditional logic.

        Args:
            answers: Dictionary of already answered questions

        Returns:
            Next SurveyQuestion or None if survey is complete
        """
        for question in self.questions:
            # Skip if already answered
            if question.question_id in answers:
                continue

            # Check if question should be shown based on conditions
            if question.should_show(answers):
                return question

        return None

    def calculate_progress(self, answers: Dict[str, Any]) -> float:
        """
        Calculate survey completion progress.

        Args:
            answers: Dictionary of answered questions

        Returns:
            Progress percentage (0-100)
        """
        # Only count questions that should be shown
        applicable_questions = [q for q in self.questions if q.should_show(answers)]

        if not applicable_questions:
            return 100.0

        answered_count = sum(1 for q in applicable_questions if q.question_id in answers)
        return (answered_count / len(applicable_questions)) * 100

    def is_complete(self, answers: Dict[str, Any]) -> bool:
        """
        Check if survey is complete.

        Args:
            answers: Dictionary of answered questions

        Returns:
            True if all applicable questions are answered
        """
        return self.get_next_question(answers) is None

    def to_dict(self) -> Dict:
        """Convert survey to dictionary."""
        return {
            "survey_id": self.survey_id,
            "title": self.title,
            "description": self.description,
            "total_questions": len(self.questions),
            "metadata": self.metadata
        }


class SurveySession:
    """
    Manages a user's progress through a survey.

    Attributes:
        session_id (str): Unique session identifier
        survey_id (str): ID of the survey being taken
        answers (dict): Dictionary of question_id -> answer
        started_at (str): ISO timestamp of session start
        completed_at (str): ISO timestamp of completion (None if incomplete)
        metadata (dict): Additional session metadata
        ai_interactions (list): Log of AI validations and follow-ups
    """

    def __init__(self, session_id: str, survey_id: str, metadata: Optional[Dict] = None):
        self.session_id = session_id
        self.survey_id = survey_id
        self.answers: Dict[str, Any] = {}
        self.started_at = datetime.utcnow().isoformat()
        self.completed_at: Optional[str] = None
        self.metadata = metadata or {}
        self.ai_interactions: List[Dict] = []

    def add_answer(self, question_id: str, answer: Any):
        """Record an answer."""
        self.answers[question_id] = answer
        logger.info(f"Session {self.session_id}: Recorded answer for {question_id}")

    def add_ai_interaction(self, interaction_type: str, question_id: str, content: str):
        """Log an AI interaction."""
        self.ai_interactions.append({
            "type": interaction_type,
            "question_id": question_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })

    def mark_complete(self):
        """Mark the session as complete."""
        self.completed_at = datetime.utcnow().isoformat()
        logger.info(f"Session {self.session_id} marked as complete")

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "survey_id": self.survey_id,
            "answers": self.answers,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
            "ai_interactions": self.ai_interactions
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SurveySession':
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            survey_id=data["survey_id"],
            metadata=data.get("metadata", {})
        )
        session.answers = data.get("answers", {})
        session.started_at = data.get("started_at", datetime.utcnow().isoformat())
        session.completed_at = data.get("completed_at")
        session.ai_interactions = data.get("ai_interactions", [])
        return session


class SurveyManager:
    """
    Manages survey definitions and sessions.
    Handles storage in Redis and provides survey lifecycle management.
    """

    def __init__(self):
        self.surveys: Dict[str, Survey] = {}
        self.session_ttl = 7 * 24 * 60 * 60  # 7 days in seconds

    def register_survey(self, survey: Survey):
        """
        Register a survey definition.

        Args:
            survey: Survey object to register
        """
        self.surveys[survey.survey_id] = survey
        logger.info(f"Registered survey: {survey.survey_id} ({survey.title})")

    def get_survey(self, survey_id: str) -> Optional[Survey]:
        """Get a registered survey by ID."""
        return self.surveys.get(survey_id)

    def list_surveys(self) -> List[Dict]:
        """Get list of all registered surveys."""
        return [survey.to_dict() for survey in self.surveys.values()]

    def create_session(self, survey_id: str, metadata: Optional[Dict] = None) -> Optional[SurveySession]:
        """
        Create a new survey session.

        Args:
            survey_id: ID of the survey to start
            metadata: Optional metadata for the session

        Returns:
            SurveySession object or None if survey not found
        """
        survey = self.get_survey(survey_id)
        if not survey:
            logger.error(f"Survey not found: {survey_id}")
            return None

        session_id = str(uuid.uuid4())
        session = SurveySession(session_id, survey_id, metadata)

        # Store in Redis
        self._save_session(session)

        logger.info(f"Created session {session_id} for survey {survey_id}")
        return session

    def get_session(self, session_id: str) -> Optional[SurveySession]:
        """
        Retrieve a session from Redis.

        Args:
            session_id: Session ID to retrieve

        Returns:
            SurveySession object or None if not found
        """
        if not redis_client:
            logger.error("Redis client not initialized")
            return None

        try:
            key = f"survey_session:{session_id}"
            data = redis_client.get(key)

            if not data:
                return None

            session_dict = json.loads(data)
            return SurveySession.from_dict(session_dict)

        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None

    def _save_session(self, session: SurveySession):
        """
        Save session to Redis.

        Args:
            session: SurveySession to save
        """
        if not redis_client:
            logger.error("Redis client not initialized")
            return

        try:
            key = f"survey_session:{session.session_id}"
            data = json.dumps(session.to_dict())
            redis_client.setex(key, self.session_ttl, data)
            logger.debug(f"Saved session {session.session_id} to Redis")

        except Exception as e:
            logger.error(f"Error saving session {session.session_id}: {e}")

    def process_answer(
        self,
        session_id: str,
        question_id: str,
        answer: Any
    ) -> Dict[str, Any]:
        """
        Process an answer and return next question.

        Args:
            session_id: Session ID
            question_id: Question being answered
            answer: User's answer

        Returns:
            Dictionary with next_question, progress, complete status, and validation
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }

        survey = self.get_survey(session.survey_id)
        if not survey:
            return {
                "success": False,
                "error": "Survey not found"
            }

        question = survey.get_question(question_id)
        if not question:
            return {
                "success": False,
                "error": "Question not found"
            }

        # Validate answer
        validation_result = self._validate_answer(question, answer, session)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["message"],
                "validation": validation_result
            }

        # Save answer
        session.add_answer(question_id, answer)

        # Generate AI follow-up if enabled
        ai_followup = None
        if question.ai_followup:
            ai_followup = self._generate_ai_followup(question, answer, session)
            if ai_followup:
                session.add_ai_interaction("followup", question_id, ai_followup)

        # Get next question
        next_question = survey.get_next_question(session.answers)
        progress = survey.calculate_progress(session.answers)
        complete = survey.is_complete(session.answers)

        if complete:
            session.mark_complete()

        # Save session
        self._save_session(session)

        result = {
            "success": True,
            "progress": progress,
            "complete": complete,
            "validation": validation_result
        }

        if ai_followup:
            result["ai_followup"] = ai_followup

        if next_question:
            result["next_question"] = next_question.to_dict(session.answers)

        return result

    def _validate_answer(
        self,
        question: SurveyQuestion,
        answer: Any,
        session: SurveySession
    ) -> Dict[str, Any]:
        """
        Validate an answer.

        Args:
            question: SurveyQuestion being answered
            answer: User's answer
            session: Current session

        Returns:
            Dictionary with valid (bool), message (str), and optional ai_feedback
        """
        # Basic validation
        if question.required and (answer is None or answer == ""):
            return {
                "valid": False,
                "message": "This question is required"
            }

        # Type-specific validation
        if question.question_type in ["multiple_choice", "rating"]:
            if answer not in question.options:
                return {
                    "valid": False,
                    "message": f"Please select one of: {', '.join(question.options)}"
                }

        # AI validation
        if question.ai_validate:
            ai_result = self._ai_validate_answer(question, answer, session)
            session.add_ai_interaction("validation", question.question_id, json.dumps(ai_result))

            if not ai_result.get("valid", True):
                return ai_result

        return {
            "valid": True,
            "message": "Answer accepted"
        }

    def _ai_validate_answer(
        self,
        question: SurveyQuestion,
        answer: Any,
        session: SurveySession
    ) -> Dict[str, Any]:
        """
        Use AI to validate answer quality.

        Args:
            question: SurveyQuestion being answered
            answer: User's answer
            session: Current session

        Returns:
            Dictionary with valid (bool), message (str), and ai_feedback
        """
        try:
            # Import here to avoid circular dependency
            from services.openrouter import call_openrouter

            # Build validation prompt
            if question.validation_prompt:
                prompt = question.validation_prompt
            else:
                prompt = f"""You are validating a survey answer.

Question: {question.text}
Answer: {answer}

Determine if this is a valid, meaningful answer. Consider:
- Is it relevant to the question?
- Does it provide useful information?
- Is it clear and understandable?
- Is it not just gibberish or a joke response?

Respond in JSON format:
{{
    "valid": true/false,
    "message": "Explanation for the user",
    "feedback": "Constructive feedback if invalid"
}}"""

            messages = [{"role": "user", "content": prompt}]

            result = call_openrouter(
                messages=messages,
                model="anthropic/claude-3.5-sonnet",
                temperature=0.3,
                max_tokens=500
            )

            if not result["success"]:
                logger.error(f"AI validation failed: {result.get('error')}")
                # Default to valid if AI fails
                return {"valid": True, "message": "Answer accepted"}

            # Parse AI response
            try:
                ai_response = json.loads(result["content"])
                return {
                    "valid": ai_response.get("valid", True),
                    "message": ai_response.get("message", "Answer accepted"),
                    "ai_feedback": ai_response.get("feedback")
                }
            except json.JSONDecodeError:
                # If AI doesn't return valid JSON, accept the answer
                return {"valid": True, "message": "Answer accepted"}

        except Exception as e:
            logger.error(f"Error in AI validation: {e}")
            # Default to valid if error occurs
            return {"valid": True, "message": "Answer accepted"}

    def _generate_ai_followup(
        self,
        question: SurveyQuestion,
        answer: Any,
        session: SurveySession
    ) -> Optional[str]:
        """
        Generate AI-powered follow-up question or comment.

        Args:
            question: SurveyQuestion that was answered
            answer: User's answer
            session: Current session

        Returns:
            Follow-up text or None
        """
        try:
            from services.openrouter import call_openrouter

            # Build context from previous answers
            survey = self.get_survey(session.survey_id)
            context = []
            for q_id, ans in session.answers.items():
                q = survey.get_question(q_id)
                if q:
                    context.append(f"Q: {q.text}\nA: {ans}")

            context_text = "\n\n".join(context) if context else "No previous answers."

            prompt = f"""You are creating an engaging survey experience. Based on the user's answer, generate a brief, personalized follow-up comment or insight.

Survey Context:
{context_text}

Current Question: {question.text}
User's Answer: {answer}

Generate a short (1-2 sentences), friendly follow-up that:
- Acknowledges their answer
- Adds value or insight
- Keeps them engaged
- Is conversational and warm

Respond with just the follow-up text, no JSON or formatting."""

            messages = [{"role": "user", "content": prompt}]

            result = call_openrouter(
                messages=messages,
                model="anthropic/claude-3.5-sonnet",
                temperature=0.7,
                max_tokens=200
            )

            if result["success"]:
                return result["content"].strip()
            else:
                logger.error(f"AI follow-up generation failed: {result.get('error')}")
                return None

        except Exception as e:
            logger.error(f"Error generating AI follow-up: {e}")
            return None


# Global survey manager instance
survey_manager = SurveyManager()


# ============================================================================
# FLASK BLUEPRINT
# ============================================================================

survey_bp = Blueprint('ai_survey', __name__)


def require_survey_manager(f):
    """Decorator to ensure survey manager is initialized."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not redis_client:
            return jsonify({
                "status": "error",
                "error": "Survey framework not initialized. Call init_dependencies() first."
            }), 500
        return f(*args, **kwargs)
    return decorated_function


@survey_bp.route("/start", methods=["POST"])
@require_survey_manager
def start_survey():
    """
    Start a new survey session.

    Request Body:
        {
            "survey_id": "customer_satisfaction",
            "metadata": {"user_id": "123", "source": "email"}
        }

    Response:
        {
            "status": "success",
            "session_id": "uuid",
            "survey": {...},
            "first_question": {...}
        }
    """
    try:
        data = request.get_json()
        survey_id = data.get("survey_id")
        metadata = data.get("metadata", {})

        if not survey_id:
            return jsonify({
                "status": "error",
                "error": "survey_id is required"
            }), 400

        # Create session
        session = survey_manager.create_session(survey_id, metadata)
        if not session:
            return jsonify({
                "status": "error",
                "error": f"Survey '{survey_id}' not found"
            }), 404

        # Get survey and first question
        survey = survey_manager.get_survey(survey_id)
        first_question = survey.get_next_question({})

        response = {
            "status": "success",
            "session_id": session.session_id,
            "survey": survey.to_dict()
        }

        if first_question:
            response["first_question"] = first_question.to_dict()

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error starting survey: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@survey_bp.route("/answer", methods=["POST"])
@require_survey_manager
def submit_answer():
    """
    Submit an answer and get next question.

    Request Body:
        {
            "session_id": "uuid",
            "question_id": "q1",
            "answer": "iPhone 15"
        }

    Response:
        {
            "status": "success",
            "next_question": {...},
            "progress": 50.0,
            "complete": false,
            "validation": {...},
            "ai_followup": "Great choice! The iPhone 15 is one of our most popular products."
        }
    """
    try:
        data = request.get_json()
        session_id = data.get("session_id")
        question_id = data.get("question_id")
        answer = data.get("answer")

        if not all([session_id, question_id]):
            return jsonify({
                "status": "error",
                "error": "session_id and question_id are required"
            }), 400

        # Process answer
        result = survey_manager.process_answer(session_id, question_id, answer)

        if not result.get("success"):
            return jsonify({
                "status": "error",
                "error": result.get("error"),
                "validation": result.get("validation")
            }), 400

        return jsonify({
            "status": "success",
            **{k: v for k, v in result.items() if k != "success"}
        }), 200

    except Exception as e:
        logger.error(f"Error submitting answer: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@survey_bp.route("/status/<session_id>", methods=["GET"])
@require_survey_manager
def get_status(session_id: str):
    """
    Get current survey session status.

    Response:
        {
            "status": "success",
            "session": {...},
            "survey": {...},
            "progress": 50.0,
            "current_question": {...},
            "complete": false
        }
    """
    try:
        session = survey_manager.get_session(session_id)
        if not session:
            return jsonify({
                "status": "error",
                "error": "Session not found"
            }), 404

        survey = survey_manager.get_survey(session.survey_id)
        if not survey:
            return jsonify({
                "status": "error",
                "error": "Survey not found"
            }), 404

        current_question = survey.get_next_question(session.answers)
        progress = survey.calculate_progress(session.answers)
        complete = survey.is_complete(session.answers)

        response = {
            "status": "success",
            "session": session.to_dict(),
            "survey": survey.to_dict(),
            "progress": progress,
            "complete": complete
        }

        if current_question:
            response["current_question"] = current_question.to_dict(session.answers)

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@survey_bp.route("/results/<session_id>", methods=["GET"])
@require_survey_manager
def get_results(session_id: str):
    """
    Get survey results for a completed session.

    Response:
        {
            "status": "success",
            "session": {...},
            "survey": {...},
            "answers": {...},
            "metadata": {...},
            "completed_at": "2025-11-14T10:30:00"
        }
    """
    try:
        session = survey_manager.get_session(session_id)
        if not session:
            return jsonify({
                "status": "error",
                "error": "Session not found"
            }), 404

        survey = survey_manager.get_survey(session.survey_id)
        if not survey:
            return jsonify({
                "status": "error",
                "error": "Survey not found"
            }), 404

        return jsonify({
            "status": "success",
            "session": session.to_dict(),
            "survey": survey.to_dict(),
            "answers": session.answers,
            "metadata": session.metadata,
            "completed_at": session.completed_at,
            "ai_interactions": session.ai_interactions
        }), 200

    except Exception as e:
        logger.error(f"Error getting results: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@survey_bp.route("/export/<session_id>", methods=["GET"])
@require_survey_manager
def export_session(session_id: str):
    """
    Export full survey session as JSON.

    Response:
        {
            "status": "success",
            "export": {
                "session": {...},
                "survey": {...},
                "questions_and_answers": [...]
            }
        }
    """
    try:
        session = survey_manager.get_session(session_id)
        if not session:
            return jsonify({
                "status": "error",
                "error": "Session not found"
            }), 404

        survey = survey_manager.get_survey(session.survey_id)
        if not survey:
            return jsonify({
                "status": "error",
                "error": "Survey not found"
            }), 404

        # Build Q&A list
        qa_list = []
        for question in survey.questions:
            if question.question_id in session.answers:
                qa_list.append({
                    "question": question.to_dict(session.answers),
                    "answer": session.answers[question.question_id]
                })

        export_data = {
            "session": session.to_dict(),
            "survey": survey.to_dict(),
            "questions_and_answers": qa_list
        }

        return jsonify({
            "status": "success",
            "export": export_data
        }), 200

    except Exception as e:
        logger.error(f"Error exporting session: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@survey_bp.route("/list", methods=["GET"])
@require_survey_manager
def list_surveys():
    """
    List all registered surveys.

    Response:
        {
            "status": "success",
            "surveys": [...]
        }
    """
    try:
        surveys = survey_manager.list_surveys()
        return jsonify({
            "status": "success",
            "surveys": surveys
        }), 200

    except Exception as e:
        logger.error(f"Error listing surveys: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_simple_survey(
    survey_id: str,
    title: str,
    questions: List[tuple],
    description: str = ""
) -> Survey:
    """
    Convenience function to create a simple linear survey.

    Args:
        survey_id: Unique survey ID
        title: Survey title
        questions: List of tuples (question_id, text, type, options, required)
        description: Survey description

    Returns:
        Survey object

    Example:
        survey = create_simple_survey(
            "nps_survey",
            "Net Promoter Score",
            [
                ("q1", "How likely are you to recommend us?", "rating",
                 ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], True),
                ("q2", "What's the main reason for your score?", "text", None, True)
            ]
        )
    """
    survey = Survey(survey_id, title, description)

    for q_data in questions:
        q_id, text, q_type = q_data[0], q_data[1], q_data[2]
        options = q_data[3] if len(q_data) > 3 else None
        required = q_data[4] if len(q_data) > 4 else True

        survey.add_question(SurveyQuestion(
            question_id=q_id,
            text=text,
            question_type=q_type,
            options=options,
            required=required
        ))

    return survey


# ============================================================================
# EXAMPLE SURVEY DEFINITIONS
# ============================================================================

def create_example_surveys():
    """
    Create example surveys to demonstrate the framework.
    Call this after init_dependencies() to have ready-to-use surveys.
    """

    # Example 1: Customer Satisfaction Survey
    customer_survey = Survey(
        survey_id="customer_satisfaction",
        title="Customer Satisfaction Survey",
        description="Help us understand your experience with our product"
    )

    customer_survey.add_question(SurveyQuestion(
        question_id="q1_product",
        text="What product did you purchase?",
        question_type="text",
        ai_validate=True,
        required=True
    ))

    customer_survey.add_question(SurveyQuestion(
        question_id="q2_satisfaction",
        text="How satisfied are you with your {q1_product}?",
        question_type="rating",
        options=["Very Unsatisfied", "Unsatisfied", "Neutral", "Satisfied", "Very Satisfied"],
        required=True
    ))

    customer_survey.add_question(SurveyQuestion(
        question_id="q3_negative_feedback",
        text="We're sorry to hear that. What could we improve about {q1_product}?",
        question_type="text",
        condition=lambda answers: answers.get("q2_satisfaction") in ["Very Unsatisfied", "Unsatisfied"],
        ai_followup=True,
        required=True
    ))

    customer_survey.add_question(SurveyQuestion(
        question_id="q3_positive_feedback",
        text="That's great! What do you love most about {q1_product}?",
        question_type="text",
        condition=lambda answers: answers.get("q2_satisfaction") in ["Satisfied", "Very Satisfied"],
        ai_followup=True,
        required=True
    ))

    customer_survey.add_question(SurveyQuestion(
        question_id="q4_recommend",
        text="Would you recommend {q1_product} to a friend?",
        question_type="yes_no",
        options=["Yes", "No"],
        required=True
    ))

    survey_manager.register_survey(customer_survey)


    # Example 2: Employee Feedback Survey
    employee_survey = Survey(
        survey_id="employee_feedback",
        title="Employee Engagement Survey",
        description="Share your thoughts about working here"
    )

    employee_survey.add_question(SurveyQuestion(
        question_id="q1_department",
        text="Which department do you work in?",
        question_type="multiple_choice",
        options=["Engineering", "Sales", "Marketing", "Customer Support", "HR", "Other"],
        required=True
    ))

    employee_survey.add_question(SurveyQuestion(
        question_id="q2_engagement",
        text="On a scale of 1-10, how engaged do you feel at work?",
        question_type="rating",
        options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        required=True
    ))

    employee_survey.add_question(SurveyQuestion(
        question_id="q3_challenges",
        text="What are your biggest challenges in the {q1_department} department?",
        question_type="text",
        ai_validate=True,
        ai_followup=True,
        required=True
    ))

    employee_survey.add_question(SurveyQuestion(
        question_id="q4_suggestions",
        text="What suggestions do you have for improving our workplace?",
        question_type="text",
        ai_followup=True,
        required=False
    ))

    survey_manager.register_survey(employee_survey)


    logger.info("Example surveys created and registered")


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
QUICK START GUIDE:

1. In your app.py, import and initialize:

    from ai_survey_framework import survey_bp, init_dependencies, create_example_surveys

    # Register blueprint
    app.register_blueprint(survey_bp, url_prefix='/api/survey')

    # Initialize with Redis client
    init_dependencies(redis_client)

    # (Optional) Create example surveys
    create_example_surveys()


2. Create your own survey:

    from ai_survey_framework import Survey, SurveyQuestion, survey_manager

    my_survey = Survey(
        survey_id="my_custom_survey",
        title="My Custom Survey",
        description="Description here"
    )

    my_survey.add_question(SurveyQuestion(
        question_id="q1",
        text="What's your favorite color?",
        question_type="text",
        ai_validate=True
    ))

    my_survey.add_question(SurveyQuestion(
        question_id="q2",
        text="Why do you like {q1}?",
        question_type="text",
        ai_followup=True
    ))

    survey_manager.register_survey(my_survey)


3. Use the API:

    # Start survey
    POST /api/survey/start
    {
        "survey_id": "my_custom_survey",
        "metadata": {"user_id": "123"}
    }

    # Submit answer
    POST /api/survey/answer
    {
        "session_id": "uuid-from-start",
        "question_id": "q1",
        "answer": "Blue"
    }

    # Get results
    GET /api/survey/results/<session_id>


4. Advanced features:

    # Conditional questions
    my_survey.add_question(SurveyQuestion(
        question_id="q3",
        text="This only shows if you said blue!",
        question_type="text",
        condition=lambda answers: answers.get("q1", "").lower() == "blue"
    ))

    # AI validation with custom prompt
    my_survey.add_question(SurveyQuestion(
        question_id="q4",
        text="Tell us about your experience",
        question_type="text",
        ai_validate=True,
        validation_prompt="Check if this is a meaningful, detailed response (at least 2 sentences)"
    ))

    # AI-generated follow-ups
    my_survey.add_question(SurveyQuestion(
        question_id="q5",
        text="What features would you like to see?",
        question_type="text",
        ai_followup=True  # AI generates personalized response
    ))


5. Frontend integration example:

    // Start survey
    const startResponse = await fetch('/api/survey/start', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            survey_id: 'customer_satisfaction',
            metadata: {user_id: userId}
        })
    });
    const {session_id, first_question} = await startResponse.json();

    // Display question and collect answer
    displayQuestion(first_question);

    // Submit answer
    const answerResponse = await fetch('/api/survey/answer', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: session_id,
            question_id: first_question.question_id,
            answer: userAnswer
        })
    });
    const {next_question, progress, complete, ai_followup} = await answerResponse.json();

    // Show AI follow-up if present
    if (ai_followup) {
        displayFollowup(ai_followup);
    }

    // Continue with next question or show completion
    if (!complete) {
        displayQuestion(next_question);
    } else {
        showCompletion();
    }
"""
