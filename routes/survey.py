"""
AI Survey Chat Blueprint
========================

Interactive AI-powered survey system where LLMs ask questions conversationally
and validate responses before proceeding to next topics.

Features:
- Create/manage survey configurations
- Select from 20+ LLM models
- Configure AI personality and behavior
- Define survey topics (mandatory/optional)
- Sequential topic validation
- Save all conversations
- View all responses
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from typing import Optional, Dict, Any, List

from flask import (
    Blueprint, request, jsonify, render_template,
    session, redirect, url_for
)
from services.openrouter import call_openrouter

logger = logging.getLogger(__name__)

# Create Blueprint
survey_bp = Blueprint('survey', __name__)

# Supabase client (will be initialized)
supabase = None
redis_client = None

# Available LLM models for survey
AVAILABLE_MODELS = [
    {"id": "anthropic/claude-opus-4-1", "name": "Claude Opus 4.1", "provider": "Anthropic", "description": "Premium reasoning model"},
    {"id": "openai/gpt-5", "name": "GPT-5", "provider": "OpenAI", "description": "Latest flagship model"},
    {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "Google", "description": "Advanced multimodal reasoning"},
    {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1", "provider": "DeepSeek", "description": "Research-oriented reasoning"},
    {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Anthropic", "description": "Balanced mid-tier model"},
    {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "OpenAI", "description": "Multimodal model"},
    {"id": "mistralai/mistral-large-latest", "name": "Mistral Large", "provider": "Mistral AI", "description": "Powerful open-source"},
    {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "Meta", "description": "Open-source large model"},
    {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "provider": "Anthropic", "description": "Fast, affordable"},
    {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI", "description": "Cost-effective mini model"},
    {"id": "google/gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "Google", "description": "Ultra-fast model"},
    {"id": "mistralai/mistral-small-latest", "name": "Mistral Small", "provider": "Mistral AI", "description": "Compact but capable"},
    {"id": "google/gemini-2.5-pro-exp-03-25:free", "name": "Gemini 2.5 Pro (Free)", "provider": "Google", "description": "Free advanced model"},
    {"id": "deepseek/deepseek-chat:free", "name": "DeepSeek Chat (Free)", "provider": "DeepSeek", "description": "Free conversation model"},
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B (Free)", "provider": "Meta", "description": "Free open-source"},
    {"id": "mistralai/mistral-small-latest:free", "name": "Mistral Small (Free)", "provider": "Mistral AI", "description": "Free compact model"},
    {"id": "qwen/qwen-2.5-coder-32b-instruct", "name": "Qwen 2.5 Coder", "provider": "Alibaba", "description": "Specialized coding model"},
    {"id": "nvidia/llama-3.1-nemotron-70b-instruct", "name": "Nemotron 70B", "provider": "NVIDIA", "description": "NVIDIA-optimized"},
]


def init_dependencies(supabase_client, redis_instance):
    """Initialize dependencies for survey blueprint"""
    global supabase, redis_client
    supabase = supabase_client
    redis_client = redis_instance
    logger.info("Survey blueprint dependencies initialized")


# ============================================================================
# AUTHENTICATION DECORATOR
# ============================================================================

def get_current_user_id() -> Optional[str]:
    """Get current user ID from session/cookie"""
    from normscout_auth import get_current_user_id as auth_get_user
    return auth_get_user()


def require_auth(f):
    """Require authentication for route"""
    from normscout_auth import require_auth as auth_require
    return auth_require(f)


# ============================================================================
# DATABASE SCHEMA (Run in Supabase SQL Editor)
# ============================================================================

"""
-- Surveys table (configurations)
CREATE TABLE IF NOT EXISTS public.surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Survey settings
    name TEXT NOT NULL DEFAULT 'Untitled Survey',
    model_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    temperature NUMERIC(3,2) DEFAULT 0.7 CHECK (temperature >= 0 AND temperature <= 2),

    -- AI personality
    character_prompt TEXT NOT NULL,
    survey_brief TEXT NOT NULL,

    -- Topics configuration
    topics JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Format: [{"name": "Name", "description": "Full name", "mandatory": true, "order": 1}]

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,

    CONSTRAINT topics_not_empty CHECK (jsonb_array_length(topics) > 0)
);

-- Survey responses table (conversations)
CREATE TABLE IF NOT EXISTS public.survey_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,

    -- Response metadata
    respondent_email TEXT,
    respondent_metadata JSONB DEFAULT '{}'::jsonb,

    -- Conversation data
    conversation JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- Format: [{"role": "assistant", "content": "...", "timestamp": "..."}]

    -- Topic progress
    current_topic_index INTEGER DEFAULT 0,
    completed_topics JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"topic": "Name", "value": "John Doe", "satisfied": true, "attempts": 1}]

    -- Status
    status TEXT DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'abandoned')),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_surveys_user_id ON surveys(user_id);
CREATE INDEX IF NOT EXISTS idx_surveys_active ON surveys(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_survey_responses_survey_id ON survey_responses(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_responses_status ON survey_responses(status);

-- RLS Policies
ALTER TABLE surveys ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_responses ENABLE ROW LEVEL SECURITY;

-- Users can only access their own surveys
CREATE POLICY "Users can manage own surveys"
ON surveys
FOR ALL
USING (auth.uid() = user_id);

-- Survey responses can be viewed by survey owner
CREATE POLICY "Survey owners can view responses"
ON survey_responses
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM surveys
        WHERE surveys.id = survey_responses.survey_id
        AND surveys.user_id = auth.uid()
    )
);

-- Anyone can create responses (for public surveys)
CREATE POLICY "Anyone can create responses"
ON survey_responses
FOR INSERT
WITH CHECK (true);

-- Only response owner or survey owner can update
CREATE POLICY "Owners can update responses"
ON survey_responses
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM surveys
        WHERE surveys.id = survey_responses.survey_id
        AND surveys.user_id = auth.uid()
    )
);

-- Auto-update updated_at
CREATE TRIGGER update_surveys_updated_at
    BEFORE UPDATE ON surveys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""


# ============================================================================
# PAGE ROUTES
# ============================================================================

@survey_bp.route('/surveycreate')
@require_auth
def survey_create_page():
    """Survey creation/management page"""
    return render_template('surveycreate.html')


@survey_bp.route('/survey')
def survey_chat_page():
    """Public survey chat interface"""
    # Get survey_id from query params
    survey_id = request.args.get('id')
    if not survey_id:
        return "Survey ID required", 400

    return render_template('survey.html', survey_id=survey_id)


@survey_bp.route('/survey-responses')
@require_auth
def survey_responses_page():
    """Survey responses viewer page"""
    # Get survey_id from query params
    survey_id = request.args.get('id')
    if not survey_id:
        return "Survey ID required", 400

    return render_template('survey_responses.html', survey_id=survey_id)


# ============================================================================
# SURVEY CRUD API
# ============================================================================

@survey_bp.route('/api/surveys/create', methods=['POST'])
@require_auth
def create_survey():
    """
    Create a new survey configuration

    Request body:
    {
        "name": "Customer Feedback Survey",
        "model_id": "anthropic/claude-3.5-sonnet",
        "model_name": "Claude 3.5 Sonnet",
        "temperature": 0.7,
        "character_prompt": "You are a friendly survey assistant...",
        "survey_brief": "This survey collects customer feedback...",
        "topics": [
            {"name": "Name", "description": "Full name", "mandatory": true, "order": 1},
            {"name": "Age", "description": "Age in years", "mandatory": false, "order": 2}
        ]
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Validate required fields
        required = ['model_id', 'model_name', 'character_prompt', 'survey_brief', 'topics']
        for field in required:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate topics
        topics = data.get('topics', [])
        if not topics or len(topics) == 0:
            return jsonify({"error": "At least one topic is required"}), 400

        # Sort topics by order
        topics.sort(key=lambda t: t.get('order', 999))

        # Create survey
        survey = {
            "user_id": user_id,
            "name": data.get('name', 'Untitled Survey'),
            "model_id": data['model_id'],
            "model_name": data['model_name'],
            "temperature": float(data.get('temperature', 0.7)),
            "character_prompt": data['character_prompt'],
            "survey_brief": data['survey_brief'],
            "topics": topics,
            "is_active": True
        }

        result = supabase.table('surveys').insert(survey).execute()

        if not result.data:
            return jsonify({"error": "Failed to create survey"}), 500

        logger.info(f"Survey created: {result.data[0]['id']}")

        return jsonify({
            "success": True,
            "survey": result.data[0]
        }), 201

    except Exception as e:
        logger.exception("Failed to create survey")
        return jsonify({"error": f"Create failed: {str(e)}"}), 500


@survey_bp.route('/api/surveys', methods=['GET'])
@require_auth
def list_surveys():
    """Get all surveys for current user"""
    try:
        user_id = get_current_user_id()

        # Get active surveys only by default
        show_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        query = supabase.table('surveys') \
            .select('*') \
            .eq('user_id', user_id)

        if not show_inactive:
            query = query.eq('is_active', True)

        query = query.order('created_at', desc=True)

        result = query.execute()

        return jsonify({
            "surveys": result.data,
            "count": len(result.data)
        })

    except Exception as e:
        logger.exception("Failed to list surveys")
        return jsonify({"error": f"List failed: {str(e)}"}), 500


@survey_bp.route('/api/surveys/<survey_id>', methods=['GET'])
def get_survey(survey_id: str):
    """Get single survey (public - no auth required for taking surveys)"""
    try:
        result = supabase.table('surveys') \
            .select('*') \
            .eq('id', survey_id) \
            .eq('is_active', True) \
            .single() \
            .execute()

        if not result.data:
            return jsonify({"error": "Survey not found or inactive"}), 404

        return jsonify(result.data)

    except Exception as e:
        logger.exception("Failed to get survey")
        return jsonify({"error": f"Get failed: {str(e)}"}), 500


@survey_bp.route('/api/surveys/<survey_id>', methods=['PUT'])
@require_auth
def update_survey(survey_id: str):
    """Update survey configuration"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Build update dict with allowed fields
        allowed_fields = ['name', 'model_id', 'model_name', 'temperature',
                         'character_prompt', 'survey_brief', 'topics', 'is_active']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Sort topics if present
        if 'topics' in update_data:
            update_data['topics'].sort(key=lambda t: t.get('order', 999))

        result = supabase.table('surveys') \
            .update(update_data) \
            .eq('id', survey_id) \
            .eq('user_id', user_id) \
            .execute()

        if not result.data:
            return jsonify({"error": "Survey not found or not authorized"}), 404

        return jsonify({
            "success": True,
            "survey": result.data[0]
        })

    except Exception as e:
        logger.exception("Failed to update survey")
        return jsonify({"error": f"Update failed: {str(e)}"}), 500


@survey_bp.route('/api/surveys/<survey_id>', methods=['DELETE'])
@require_auth
def delete_survey(survey_id: str):
    """Delete (deactivate) survey"""
    try:
        user_id = get_current_user_id()

        # Soft delete by setting is_active to false
        result = supabase.table('surveys') \
            .update({"is_active": False}) \
            .eq('id', survey_id) \
            .eq('user_id', user_id) \
            .execute()

        if not result.data:
            return jsonify({"error": "Survey not found or not authorized"}), 404

        return jsonify({"success": True})

    except Exception as e:
        logger.exception("Failed to delete survey")
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500


# ============================================================================
# SURVEY RESPONSE API
# ============================================================================

@survey_bp.route('/api/surveys/<survey_id>/responses', methods=['GET'])
@require_auth
def get_survey_responses(survey_id: str):
    """Get all responses for a survey"""
    try:
        user_id = get_current_user_id()

        # Verify user owns this survey
        survey = supabase.table('surveys') \
            .select('id') \
            .eq('id', survey_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        if not survey.data:
            return jsonify({"error": "Survey not found or not authorized"}), 404

        # Get responses
        result = supabase.table('survey_responses') \
            .select('*') \
            .eq('survey_id', survey_id) \
            .order('started_at', desc=True) \
            .execute()

        return jsonify({
            "responses": result.data,
            "count": len(result.data)
        })

    except Exception as e:
        logger.exception("Failed to get responses")
        return jsonify({"error": f"Get failed: {str(e)}"}), 500


@survey_bp.route('/api/surveys/<survey_id>/start', methods=['POST'])
def start_survey_response(survey_id: str):
    """Start a new survey response (create conversation)"""
    try:
        data = request.get_json() or {}

        # Verify survey exists and is active
        survey = supabase.table('surveys') \
            .select('*') \
            .eq('id', survey_id) \
            .eq('is_active', True) \
            .single() \
            .execute()

        if not survey.data:
            return jsonify({"error": "Survey not found or inactive"}), 404

        survey_data = survey.data
        topics = survey_data['topics']

        # Create response record
        response = {
            "survey_id": survey_id,
            "respondent_email": data.get('email'),
            "respondent_metadata": data.get('metadata', {}),
            "conversation": [],
            "current_topic_index": 0,
            "completed_topics": [],
            "status": "in_progress"
        }

        result = supabase.table('survey_responses').insert(response).execute()

        if not result.data:
            return jsonify({"error": "Failed to start survey"}), 500

        response_id = result.data[0]['id']

        # Generate first message from AI
        first_topic = topics[0]
        first_message = generate_initial_message(survey_data, first_topic)

        # Save AI message to conversation
        conversation = [{
            "role": "assistant",
            "content": first_message,
            "timestamp": datetime.utcnow().isoformat(),
            "topic": first_topic['name']
        }]

        supabase.table('survey_responses') \
            .update({
                "conversation": conversation,
                "last_interaction_at": datetime.utcnow().isoformat()
            }) \
            .eq('id', response_id) \
            .execute()

        logger.info(f"Survey response started: {response_id}")

        return jsonify({
            "success": True,
            "response_id": response_id,
            "message": first_message
        })

    except Exception as e:
        logger.exception("Failed to start survey response")
        return jsonify({"error": f"Start failed: {str(e)}"}), 500


@survey_bp.route('/api/responses/<response_id>/message', methods=['POST'])
def submit_message(response_id: str):
    """
    Submit user message and get AI response

    Request body:
    {
        "message": "My name is John Doe"
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Get response record
        response = supabase.table('survey_responses') \
            .select('*, surveys(*)') \
            .eq('id', response_id) \
            .single() \
            .execute()

        if not response.data:
            return jsonify({"error": "Response not found"}), 404

        response_data = response.data
        survey_data = response_data['surveys']

        # Check if completed
        if response_data['status'] == 'completed':
            return jsonify({"error": "Survey already completed"}), 400

        # Add user message to conversation
        conversation = response_data['conversation']
        conversation.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Get current topic
        current_index = response_data['current_topic_index']
        topics = survey_data['topics']

        if current_index >= len(topics):
            # Survey completed
            supabase.table('survey_responses') \
                .update({
                    "conversation": conversation,
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "last_interaction_at": datetime.utcnow().isoformat()
                }) \
                .eq('id', response_id) \
                .execute()

            return jsonify({
                "success": True,
                "completed": True,
                "message": "Thank you for completing the survey!"
            })

        current_topic = topics[current_index]

        # Validate response with LLM
        validation_result = validate_topic_response(
            survey_data,
            current_topic,
            user_message,
            conversation
        )

        satisfied = validation_result['satisfied']
        ai_response = validation_result['message']
        extracted_value = validation_result.get('extracted_value', user_message)

        # Add AI response to conversation
        conversation.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat(),
            "topic": current_topic['name'],
            "validation": {
                "satisfied": satisfied,
                "extracted_value": extracted_value
            }
        })

        # Update response record
        update_data = {
            "conversation": conversation,
            "last_interaction_at": datetime.utcnow().isoformat()
        }

        if satisfied:
            # Move to next topic
            completed_topics = response_data['completed_topics']
            completed_topics.append({
                "topic": current_topic['name'],
                "value": extracted_value,
                "satisfied": True,
                "completed_at": datetime.utcnow().isoformat()
            })

            next_index = current_index + 1
            update_data['completed_topics'] = completed_topics
            update_data['current_topic_index'] = next_index

            # Check if all topics completed
            if next_index >= len(topics):
                update_data['status'] = 'completed'
                update_data['completed_at'] = datetime.utcnow().isoformat()

        supabase.table('survey_responses') \
            .update(update_data) \
            .eq('id', response_id) \
            .execute()

        return jsonify({
            "success": True,
            "message": ai_response,
            "satisfied": satisfied,
            "completed": update_data.get('status') == 'completed',
            "current_topic_index": update_data.get('current_topic_index', current_index),
            "total_topics": len(topics)
        })

    except Exception as e:
        logger.exception("Failed to submit message")
        return jsonify({"error": f"Submit failed: {str(e)}"}), 500


# ============================================================================
# LLM HELPERS
# ============================================================================

def generate_initial_message(survey_data: Dict, first_topic: Dict) -> str:
    """Generate the first message from AI to start the survey"""
    character_prompt = survey_data['character_prompt']
    survey_brief = survey_data['survey_brief']
    topic_name = first_topic['name']
    topic_desc = first_topic.get('description', topic_name)

    prompt = f"""{character_prompt}

SURVEY CONTEXT:
{survey_brief}

You are starting a survey conversation. Your first task is to ask about: {topic_name} ({topic_desc}).

Generate a friendly, engaging opening message that:
1. Briefly introduces yourself and the survey (1-2 sentences max)
2. Asks for the first piece of information: {topic_name}

Keep it conversational and natural. Don't mention "topics" or "validation" - just have a natural conversation.

Generate ONLY the message, nothing else:"""

    messages = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages,
        model=survey_data['model_id'],
        temperature=survey_data['temperature'],
        max_tokens=200
    )

    if result.get('success'):
        return result['content'].strip()
    else:
        # Fallback message
        return f"Hello! I'd like to learn more about you. Let's start - can you tell me your {topic_name.lower()}?"


def validate_topic_response(
    survey_data: Dict,
    topic: Dict,
    user_message: str,
    conversation: List[Dict]
) -> Dict:
    """
    Validate user's response for current topic using LLM

    Returns:
    {
        "satisfied": bool,
        "message": str,  # AI's response
        "extracted_value": str  # Cleaned/extracted value
    }
    """
    character_prompt = survey_data['character_prompt']
    topic_name = topic['name']
    topic_desc = topic.get('description', topic_name)
    is_mandatory = topic.get('mandatory', True)

    # Build conversation context
    recent_conv = conversation[-6:] if len(conversation) > 6 else conversation
    conv_context = "\n".join([
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in recent_conv
    ])

    prompt = f"""{character_prompt}

CURRENT TOPIC: {topic_name}
DESCRIPTION: {topic_desc}
MANDATORY: {"Yes" if is_mandatory else "No"}

CONVERSATION SO FAR:
{conv_context}
USER: {user_message}

YOUR TASK:
1. Determine if the user provided valid information for "{topic_name}"
2. If valid and sufficient, extract the clean value and move on
3. If invalid or unclear, ask for clarification naturally

VALIDATION RULES:
- For mandatory topics: Must have clear, specific information
- For optional topics: Can skip if user explicitly indicates they don't want to answer
- Reject vague answers like "maybe", "I don't know" for mandatory topics
- Accept reasonable answers even if not perfect

RESPONSE FORMAT (JSON):
{{
    "satisfied": true/false,
    "extracted_value": "cleaned value or original message",
    "message": "Your natural conversational response"
}}

If satisfied=true:
- Thank them briefly
- Ask about the NEXT topic naturally (you'll be told what's next)
- Keep it conversational

If satisfied=false:
- Politely ask for clarification
- Be specific about what you need
- Stay in character

Generate ONLY the JSON, nothing else:"""

    messages = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages,
        model=survey_data['model_id'],
        temperature=survey_data['temperature'],
        max_tokens=300
    )

    if not result.get('success'):
        # Fallback: accept the answer
        return {
            "satisfied": True,
            "extracted_value": user_message,
            "message": "Thank you! Let's move on to the next question."
        }

    try:
        # Parse JSON response
        content = result['content'].strip()
        # Try to extract JSON if wrapped in markdown
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        validation = json.loads(content)

        # If satisfied and there's a next topic, append next topic question
        if validation.get('satisfied'):
            # Get next topic from survey
            current_index = None
            topics = survey_data['topics']
            for i, t in enumerate(topics):
                if t['name'] == topic_name:
                    current_index = i
                    break

            if current_index is not None and current_index + 1 < len(topics):
                next_topic = topics[current_index + 1]
                next_prompt = f"\n\nNow, could you tell me about your {next_topic['name'].lower()}?"
                validation['message'] = validation['message'].strip() + next_prompt

        return validation

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Failed to parse validation JSON: {e}")
        # Fallback: extract from text
        content = result['content'].lower()
        if any(word in content for word in ['yes', 'great', 'perfect', 'thank', 'good']):
            return {
                "satisfied": True,
                "extracted_value": user_message,
                "message": result['content']
            }
        else:
            return {
                "satisfied": False,
                "extracted_value": user_message,
                "message": result['content']
            }


# ============================================================================
# AVAILABLE MODELS API
# ============================================================================

@survey_bp.route('/api/models', methods=['GET'])
def get_available_models():
    """Get list of available LLM models"""
    return jsonify({
        "models": AVAILABLE_MODELS,
        "count": len(AVAILABLE_MODELS)
    })
