"""
AI Survey Chat Service
Manages conversational surveys with topic-based data gathering
Uses OpenRouter LLM to conduct natural, engaging survey conversations
"""
import logging
import json
from .openrouter import call_openrouter

logger = logging.getLogger(__name__)


def analyze_topic_completion(
    messages: list,
    topic: dict,
    character_prompt: str,
    survey_explanation: str
) -> dict:
    """
    Analyze if the current topic has been sufficiently answered.

    Args:
        messages: Conversation history [{"role": "user/assistant", "content": "..."}]
        topic: Topic dict {"name": "Age", "mandatory": true, "order": 1}
        character_prompt: Character/persona for the AI
        survey_explanation: Context about why gathering this data

    Returns:
        {
            "is_complete": bool,
            "extracted_data": str or None,
            "reasoning": str,
            "attempts": int
        }
    """
    # Build conversation context (last 10 messages for this topic)
    conversation_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in messages[-10:]
    ])

    topic_name = topic['name']
    is_mandatory = topic.get('mandatory', False)

    prompt = f"""You are analyzing a survey conversation to determine if a specific topic has been answered.

SURVEY CONTEXT:
{survey_explanation}

CURRENT TOPIC: {topic_name}
MANDATORY: {"Yes - must be answered" if is_mandatory else "No - optional"}

CHARACTER PERSONA:
{character_prompt}

CONVERSATION:
{conversation_text}

TASK: Determine if the user has provided a clear answer for "{topic_name}".

EVALUATION CRITERIA:
- Has the user given a specific, usable answer? (not vague like "I don't know" or "maybe later")
- Is the answer relevant to the topic "{topic_name}"?
- For mandatory topics: Be thorough but reasonable (name can be "John", age can be "30s")
- For optional topics: Accept any attempt to answer or explicit decline

RESPONSE FORMAT (use exact format):
COMPLETE: yes/no
DATA: [extracted answer, or "SKIPPED" if user declined optional topic, or "UNCLEAR" if incomplete]
REASONING: [brief explanation]
ATTEMPTS: [estimated number of times this topic was asked in the conversation]

Examples:
- For "Name" topic with answer "My name is Sarah" → COMPLETE: yes, DATA: Sarah
- For "Age" topic with answer "I'm not comfortable sharing that" on optional → COMPLETE: yes, DATA: SKIPPED
- For "Age" topic with answer "I'm not sure" on mandatory → COMPLETE: no, DATA: UNCLEAR
- For "Hobbies" with answer "I like reading and hiking" → COMPLETE: yes, DATA: reading and hiking
"""

    messages_for_llm = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages_for_llm,
        model="openai/gpt-4o-mini",  # Fast and cost-effective for validation
        temperature=0.3,
        max_tokens=200
    )

    if not result["success"]:
        logger.error(f"Topic completion analysis failed: {result.get('error')}")
        return {
            "is_complete": False,
            "extracted_data": None,
            "reasoning": f"Error: {result.get('error')}",
            "attempts": 0
        }

    # Parse response
    response = result["content"]
    lines = response.strip().split("\n")
    is_complete = False
    extracted_data = None
    reasoning = ""
    attempts = 1

    for line in lines:
        if "COMPLETE:" in line.upper():
            is_complete = "yes" in line.lower()
        elif "DATA:" in line.upper():
            data_text = line.split(":", 1)[1].strip()
            if data_text not in ["UNCLEAR", "unclear"]:
                extracted_data = data_text if data_text != "SKIPPED" else None
        elif "REASONING:" in line.upper():
            reasoning = line.split(":", 1)[1].strip()
        elif "ATTEMPTS:" in line.upper():
            try:
                attempts = int(line.split(":", 1)[1].strip())
            except:
                attempts = 1

    return {
        "is_complete": is_complete,
        "extracted_data": extracted_data,
        "reasoning": reasoning,
        "attempts": attempts
    }


def generate_survey_question(
    config: dict,
    topic: dict,
    messages: list,
    attempt_count: int = 1
) -> str:
    """
    Generate a natural, character-driven question for the current topic.

    Args:
        config: Survey configuration (model, temperature, character_prompt, explanation)
        topic: Current topic {"name": "...", "mandatory": ...}
        messages: Conversation history
        attempt_count: How many times we've asked about this topic (1 = first time)

    Returns:
        Natural question string
    """
    character_prompt = config.get('character_prompt', 'You are a friendly survey assistant.')
    survey_explanation = config.get('survey_explanation', '')
    topic_name = topic['name']
    is_mandatory = topic.get('mandatory', False)

    # Build conversation context (last 6 messages)
    conversation_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in messages[-6:]
    ]) if messages else "No conversation yet."

    prompt = f"""You are conducting a survey with this persona:
{character_prompt}

SURVEY PURPOSE:
{survey_explanation}

CURRENT TOPIC TO ASK ABOUT: {topic_name}
MANDATORY: {"Yes - required" if is_mandatory else "No - optional"}
ATTEMPT: {attempt_count} (1 = first time asking, 2+ = follow-up)

CONVERSATION SO FAR:
{conversation_text}

TASK: Generate ONE natural, engaging question to gather information about "{topic_name}".

RULES:
- Stay in character according to your persona
- Be conversational and friendly
- For attempt 1: Ask directly and naturally
- For attempt 2+: Acknowledge their previous response and gently clarify or rephrase
- For optional topics: Make it clear they can skip ("feel free to skip if you'd prefer")
- Keep it brief and focused (1-2 sentences max)
- Use examples when helpful (e.g., "like 'software engineer' or 'student'")
- Don't ask multiple questions at once

QUESTION:"""

    messages_for_llm = [{"role": "user", "content": prompt}]

    # Use the configured model and temperature for the actual survey
    model = config.get('model', 'openai/gpt-4o-mini')
    temperature = config.get('temperature', 0.7)

    result = call_openrouter(
        messages_for_llm,
        model=model,
        temperature=temperature,
        max_tokens=150
    )

    if not result["success"]:
        logger.error(f"Question generation failed: {result.get('error')}")
        # Return a generic question
        if attempt_count > 1:
            return f"I'd love to know more about your {topic_name.lower()}. Could you share that with me?"
        else:
            return f"Could you tell me about your {topic_name.lower()}?"

    # Clean up the response
    question = result["content"].strip()
    if question.startswith("QUESTION:"):
        question = question.replace("QUESTION:", "").strip()

    return question


def generate_welcome_message(config: dict) -> str:
    """
    Generate an engaging welcome message for the survey.

    Args:
        config: Survey configuration

    Returns:
        Welcome message string
    """
    character_prompt = config.get('character_prompt', 'You are a friendly survey assistant.')
    survey_explanation = config.get('survey_explanation', '')
    topics = config.get('topics', [])

    prompt = f"""You are starting a survey conversation with this persona:
{character_prompt}

SURVEY PURPOSE:
{survey_explanation}

NUMBER OF TOPICS: {len(topics)}

TASK: Generate a warm, engaging welcome message to start the survey.

RULES:
- Stay in character
- Be friendly and put the user at ease
- Briefly mention why you're gathering this information (if explanation provided)
- Keep it conversational (2-3 sentences)
- Don't list all the topics
- End with an invitation to start

WELCOME MESSAGE:"""

    messages = [{"role": "user", "content": prompt}]

    model = config.get('model', 'openai/gpt-4o-mini')
    temperature = config.get('temperature', 0.7)

    result = call_openrouter(
        messages,
        model=model,
        temperature=temperature,
        max_tokens=150
    )

    if not result["success"]:
        logger.error(f"Welcome message generation failed: {result.get('error')}")
        return "Hi! I'd love to learn a bit more about you. Shall we get started?"

    welcome = result["content"].strip()
    if welcome.startswith("WELCOME MESSAGE:"):
        welcome = welcome.replace("WELCOME MESSAGE:", "").strip()

    return welcome


def generate_completion_message(config: dict, gathered_data: dict) -> str:
    """
    Generate a thank you / completion message.

    Args:
        config: Survey configuration
        gathered_data: All data gathered {"Name": "John", "Age": "30", ...}

    Returns:
        Completion message string
    """
    character_prompt = config.get('character_prompt', 'You are a friendly survey assistant.')

    # Build summary of what was gathered
    data_summary = "\n".join([f"- {topic}: {value}" for topic, value in gathered_data.items()])

    prompt = f"""You are completing a survey conversation with this persona:
{character_prompt}

DATA GATHERED:
{data_summary}

TASK: Generate a warm, appreciative closing message to thank the user.

RULES:
- Stay in character
- Express genuine gratitude
- Keep it brief and positive (1-2 sentences)
- Don't repeat all the data back to them
- Make them feel their input was valuable

COMPLETION MESSAGE:"""

    messages = [{"role": "user", "content": prompt}]

    model = config.get('model', 'openai/gpt-4o-mini')
    temperature = config.get('temperature', 0.7)

    result = call_openrouter(
        messages,
        model=model,
        temperature=temperature,
        max_tokens=100
    )

    if not result["success"]:
        logger.error(f"Completion message generation failed: {result.get('error')}")
        return "Thank you so much for your time! Your responses have been recorded."

    completion = result["content"].strip()
    if completion.startswith("COMPLETION MESSAGE:"):
        completion = completion.replace("COMPLETION MESSAGE:", "").strip()

    return completion


def check_mandatory_topics(topics: list, completed_topics: dict) -> dict:
    """
    Check if all mandatory topics have been completed.

    Args:
        topics: List of topic dicts [{"name": "...", "mandatory": true}, ...]
        completed_topics: Dict of completed topics {"Name": {...}, "Age": {...}}

    Returns:
        {
            "all_mandatory_complete": bool,
            "missing_mandatory": [topic_names]
        }
    """
    missing_mandatory = []

    for topic in topics:
        if topic.get('mandatory', False):
            topic_name = topic['name']
            if topic_name not in completed_topics:
                missing_mandatory.append(topic_name)
            elif not completed_topics[topic_name].get('completed', False):
                missing_mandatory.append(topic_name)

    return {
        "all_mandatory_complete": len(missing_mandatory) == 0,
        "missing_mandatory": missing_mandatory
    }


def calculate_completion_percentage(topics: list, completed_topics: dict) -> float:
    """
    Calculate survey completion percentage.

    Args:
        topics: List of all topics
        completed_topics: Dict of completed topics

    Returns:
        Percentage (0-100)
    """
    if not topics:
        return 100.0

    total_topics = len(topics)
    completed_count = sum(
        1 for topic in topics
        if topic['name'] in completed_topics and completed_topics[topic['name']].get('completed', False)
    )

    return round((completed_count / total_topics) * 100, 2)


def extract_structured_data(completed_topics: dict) -> dict:
    """
    Extract clean structured data from completed topics.

    Args:
        completed_topics: {"Name": {"completed": true, "data": "John", ...}, ...}

    Returns:
        Clean dict: {"Name": "John", "Age": "30", ...}
    """
    structured_data = {}

    for topic_name, topic_info in completed_topics.items():
        if topic_info.get('completed', False):
            data = topic_info.get('data')
            if data and data != "SKIPPED":
                structured_data[topic_name] = data

    return structured_data
