"""
Conversational product information gathering using LLM
Keeps the conversation natural and asks clarifying questions when needed
Migrated from NormScout_Test/AICore - adapted for web use
"""
import logging
from .openrouter import call_openrouter

logger = logging.getLogger(__name__)


def analyze_completeness(conversation_history: list) -> dict:
    """
    Ask LLM if we have enough information for accurate norm matching.

    Args:
        conversation_history: List of {"role": "user"/"assistant", "content": "..."}

    Returns:
        {
            "is_complete": bool,
            "missing_info": list,
            "reasoning": str
        }
    """
    # Build conversation context
    conversation_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in conversation_history
    ])

    prompt = f"""You are an EU compliance expert. Review this product conversation and determine if we have enough information for accurate compliance norm matching.

CONVERSATION:
{conversation_text}

CRITICAL INFORMATION NEEDED:
1. Is it an electrical/electronic product? (yes/no)
2. Power source (battery, mains AC, USB, PoE, solar, etc.)
3. Voltage/current specifications (especially for mains-powered devices)
4. Wireless features (WiFi, Bluetooth, cellular, none, etc.)
5. Product category (lighting, IoT, IT equipment, household appliance, etc.)
6. For battery devices: rechargeable or disposable? If rechargeable, how is it charged?

RESPONSE FORMAT (use exact format):
COMPLETE: yes/no
MISSING: comma-separated list of missing info (or "none" if complete)
REASONING: brief explanation

Be practical - if we have the essentials (power, voltage if applicable, wireless, category), we're good to go."""

    messages = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.3,
        max_tokens=300
    )

    if not result["success"]:
        logger.error(f"Completeness analysis failed: {result.get('error')}")
        # Default to not complete on error
        return {
            "is_complete": False,
            "missing_info": ["Error analyzing completeness"],
            "reasoning": f"Error: {result.get('error')}"
        }

    # Parse response
    response = result["content"]
    lines = response.strip().split("\n")
    is_complete = False
    missing = []
    reasoning = ""

    for line in lines:
        if "COMPLETE:" in line.upper():
            is_complete = "yes" in line.lower()
        elif "MISSING:" in line.upper():
            missing_text = line.split(":", 1)[1].strip()
            if missing_text.lower() != "none":
                missing = [m.strip() for m in missing_text.split(",")]
        elif "REASONING:" in line.upper():
            reasoning = line.split(":", 1)[1].strip()

    return {
        "is_complete": is_complete,
        "missing_info": missing,
        "reasoning": reasoning
    }


def generate_next_question(conversation_history: list, missing_info: list) -> str:
    """
    Generate a natural, conversational follow-up question.

    Args:
        conversation_history: List of conversation messages
        missing_info: List of missing information items

    Returns:
        Natural follow-up question as string
    """
    conversation_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in conversation_history
    ])

    missing_text = ", ".join(missing_info) if missing_info else "general details"

    prompt = f"""You are a friendly EU compliance expert having a conversation with a developer about their product.

CONVERSATION SO FAR:
{conversation_text}

WHAT'S STILL UNCLEAR:
{missing_text}

Generate ONE natural, conversational follow-up question to clarify the MOST important missing detail.

RULES:
- Be friendly and conversational (like "Are we thinking rechargeable batteries or disposable ones?")
- Ask about the most critical missing piece first
- Keep it short and simple
- Don't ask multiple questions at once
- Use examples when helpful (e.g., "USB-C, micro-USB, or another type?")
- Build on what they've already told you

QUESTION:"""

    messages = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.7,
        max_tokens=150
    )

    if not result["success"]:
        logger.error(f"Question generation failed: {result.get('error')}")
        # Return a generic question
        return "Could you tell me more about the technical specifications?"

    # Clean up the response
    question = result["content"].strip()
    if question.startswith("QUESTION:"):
        question = question.replace("QUESTION:", "").strip()

    return question


def build_final_summary(conversation_history: list) -> str:
    """
    Build a comprehensive product description from the conversation.

    Args:
        conversation_history: List of conversation messages

    Returns:
        Comprehensive product description string
    """
    conversation_text = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in conversation_history
    ])

    prompt = f"""You are an EU compliance expert. Based on this conversation, create a comprehensive technical product description.

CONVERSATION:
{conversation_text}

Create a detailed product summary that includes:
- Product type and category
- Power source and specifications (voltage, current, watts)
- Wireless features (if any)
- Battery details (type, capacity, charging method)
- Intended use and environment
- Any other relevant technical details

Write it as a clear, structured technical description suitable for compliance assessment.

PRODUCT DESCRIPTION:"""

    messages = [{"role": "user", "content": prompt}]

    result = call_openrouter(
        messages,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.5,
        max_tokens=500
    )

    if not result["success"]:
        logger.error(f"Summary generation failed: {result.get('error')}")
        # Fall back to basic concatenation
        user_messages = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        return " ".join(user_messages)

    # Clean up
    description = result["content"].strip()
    if description.startswith("PRODUCT DESCRIPTION:"):
        description = description.replace("PRODUCT DESCRIPTION:", "").strip()

    return description
