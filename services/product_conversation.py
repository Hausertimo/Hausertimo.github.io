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


def answer_analysis_question(
    product_description: str,
    matched_norms: list,
    all_norms: list,
    question: str,
    qa_history: list = None
) -> dict:
    """
    Answer user questions about completed compliance analysis.

    Args:
        product_description: The final product summary
        matched_norms: Norms that applied (confidence > threshold)
        all_norms: ALL norm check results including rejected ones
        question: User's question about the analysis
        qa_history: Previous Q&A pairs for conversation context

    Returns:
        {
            "answer": str,
            "relevant_norms": [norm_ids],
            "confidence": int
        }
    """
    import json

    # Build context - separate matched and rejected norms
    matched_ids = [n['norm_id'] for n in matched_norms]
    rejected_norms = [n for n in all_norms if n['norm_id'] not in matched_ids]

    # Prepare norm context (show samples to stay within token limits)
    matched_context = json.dumps(matched_norms[:20], indent=2) if len(matched_norms) > 0 else "None"
    rejected_context = json.dumps(rejected_norms[:10], indent=2) if len(rejected_norms) > 0 else "None"

    system_prompt = f"""You are an EU compliance expert helping users understand and optimize their product's compliance requirements.

PRODUCT:
{product_description}

APPLICABLE NORMS ({len(matched_norms)} total):
{matched_context}

REJECTED NORMS ({len(rejected_norms)} total, showing first 10):
{rejected_context}

YOUR ROLE:
- Provide clear, accurate answers based on the analysis results
- Reference specific norms by their ID (e.g., "EN 62368-1") when relevant
- If asked "why", quote the reasoning field from the norm analysis
- If asked about consequences, explain legal/business implications
- If asked about missing norms, check the rejected list

HELPING USERS REDUCE COMPLIANCE BURDEN (LEGITIMATELY):
- When users ask about reducing applicable norms, suggest LEGITIMATE design changes:
  * "You could reduce voltage from X to Y to avoid needing Z certification"
  * "Dropping the current to X would exempt you from norm Y"
  * "Changing from AC to DC power might eliminate several electrical safety requirements"
  * "Using materials rated below X temperature can simplify fire safety testing"
  * "Reducing wireless transmission power below X can avoid RF exposure testing"
- NEVER suggest circumventing or cheating on requirements
- ALWAYS explain the trade-offs (e.g., reduced functionality, market limitations)
- Make it clear these are design optimization strategies, not compliance shortcuts
- Be helpful and solution-oriented while maintaining safety and legal integrity

MODIFYING PRODUCT SPECIFICATIONS - CRITICAL INSTRUCTIONS:

When users request ANY product modification, you MUST generate the updated description. Trigger phrases include:
- "Can you change..." / "Please change..." / "Change it to..."
- "Can you adjust..." / "Please adjust..." / "Adjust it..."
- "Can you modify..." / "Modify the..." / "Update it to..."
- "Make it..." / "Set it to..." / "Switch to..."
- "Reduce..." / "Increase..." / "Lower..." / "Raise..."

When you detect a modification request, follow this EXACT pattern:

1. ACKNOWLEDGE THE CHANGE:
   Start with: "I can update your product to [describe change]."

2. EXPLAIN IMPLICATIONS (2-3 sentences):
   **Technical Changes:**
   - List what will change specifically

   **Compliance Impact:**
   - Which norms might drop off or still apply

   **Trade-offs (if any):**
   - Mention any functionality or market limitations

3. GENERATE THE COMPLETE NEW DESCRIPTION:
   Use this EXACT format - DO NOT SKIP THIS:

   ---NEW_DESCRIPTION---
   [Write the COMPLETE product description with all changes applied. Include ALL original details that aren't changing. This should be a full replacement of the current description.]
   ---END_DESCRIPTION---

4. ASK FOR CONFIRMATION:
   End with: "Would you like me to apply these changes to your product?"

EXAMPLE INTERACTION:

User: "Can you change it to run on 230V only?"
You: "I can update your product to operate on 230V AC only instead of dual voltage.

**Technical Changes:**
- Input voltage: 100-240V AC → 230V AC only (50/60Hz)
- Simplified power supply design for single voltage

**Compliance Impact:**
- Still complies with Low Voltage Directive 2014/35/EU
- Simpler testing (only 230V range instead of full range)
- May simplify EMC testing parameters

**Trade-offs:**
- Cannot be used in regions with 110V/120V power (North America, Japan)
- Limited to EU/UK/AU markets

---NEW_DESCRIPTION---
Commercial beverage dispenser with integrated cooling and WiFi connectivity
- Input: AC 230V, 50/60Hz (EU standard)
- Power consumption: [maintain from original]
- Output: [maintain from original]
- Dimensions: [maintain from original]
- WiFi: [maintain from original]
- Features: [maintain all original features]
- Target market: Food service establishments, cafes, restaurants (EU region)
---END_DESCRIPTION---

Would you like me to apply these changes to your product?"

AFTER USER CONFIRMS (says "yes", "apply it", "do it", "go ahead", "adjust it for me"):
   Say: "✅ I've updated your product description. Would you like me to re-analyze the compliance norms now?"

CRITICAL RULES:
- ALWAYS generate ---NEW_DESCRIPTION--- when user requests a modification
- If user says "adjust it for me" or "can you do it", that means APPLY THE CHANGE - generate the description
- Include the COMPLETE description, not just changed parts
- Never give general advice when user explicitly asks you to make a change
- The description must be detailed enough to replace the current one entirely

Be helpful, clear, and always generate the new description when modifications are requested."""

    # Build message history with system prompt + previous Q&A + new question
    messages = [{"role": "system", "content": system_prompt}]

    # Add previous conversation history if available (increased to 10 pairs for better context)
    if qa_history:
        for qa in qa_history[-10:]:  # Last 10 Q&A pairs for better conversation tracking
            messages.append({"role": "user", "content": qa.get("question", "")})
            messages.append({"role": "assistant", "content": qa.get("answer", "")})
    # Add current question
    messages.append({"role": "user", "content": question})

    result = call_openrouter(
        messages,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.7,  # Slightly higher for more creative suggestions
        max_tokens=1000  # Increased for more detailed answers
    )

    if not result["success"]:
        logger.error(f"Q&A failed: {result.get('error')}")
        return {
            "answer": "I'm having trouble answering that question right now. Please try rephrasing or ask another question.",
            "relevant_norms": [],
            "confidence": 0
        }

    # Extract answer text
    answer_text = result["content"]

    # Check if AI proposed a product modification
    import re
    proposed_description = None
    clean_answer = answer_text

    desc_match = re.search(r'---NEW_DESCRIPTION---(.*?)---END_DESCRIPTION---', answer_text, re.DOTALL)
    if desc_match:
        proposed_description = desc_match.group(1).strip()
        # Remove the description block from the display answer (user will see it in UI)
        clean_answer = re.sub(r'---NEW_DESCRIPTION---.*?---END_DESCRIPTION---', '', answer_text, flags=re.DOTALL).strip()
        logger.info(f"AI proposed product modification: {len(proposed_description)} chars")

    # Extract norm IDs mentioned in the answer
    relevant_norms = []
    norm_pattern = r'\b[A-Z]{2}[\s\-]?\d{4,5}[\-\d]*\b'
    found_ids = re.findall(norm_pattern, answer_text)
    relevant_norms = list(set(found_ids))  # Remove duplicates

    response = {
        "answer": clean_answer,
        "relevant_norms": relevant_norms,
        "confidence": 85  # High confidence for factual Q&A based on analysis
    }

    # Include proposed description if present
    if proposed_description:
        response["proposed_description"] = proposed_description

    return response
