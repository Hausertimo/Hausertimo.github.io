import requests
import time
import re
from typing import List, Dict, Union

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_API_URL,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_FREQUENCY_PENALTY,
    DEFAULT_PRESENCE_PENALTY,
)

# Patterns to detect AI refusals (same as async version)
REFUSAL_PATTERNS = [
    # General refusals
    r"\bsorry,? i can'?t (continue|help|do that|comply|assist|provide that|fulfill your request)",
    r"\bi'?m sorry,? but i can'?t",
    r"\bi'?m unable to",
    r"\bi'?m not able to",
    r"\bi cannot (do that|help with that|provide that|assist with that)",
    r"\bcan'?t do that rn",
    r"\bas a (language model|ai|ai model|artificial intelligence)",
    r"\bi'?m here to (support|chat|listen|help) you",
    r"\bif you want to talk,? need advice",
    r"\bi'?m all ears",
    r"^sorry\b",
    r"^i'?m sorry\b",

    # Content policy refusals
    r"\bi (am|'m|'m) not (able|allowed|permitted|authorized) to (provide|generate|create|share|discuss|assist with) (that|this|such) (content|information|material|request|topic|subject)",
    r"\bmy programming prevents me from (doing|providing|generating|sharing|discussing) (that|this|such) (content|information|material|request|topic|subject)",
    r"\bi must (decline|refuse|avoid) (your|this) request (as it|because it|since it) (violates|goes against|is against) (my|openai|company|content) (guidelines|policies|rules|terms of service)",
    r"\bi cannot assist with (that|this|such) (request|topic|subject|content) due to (ethical|legal|safety|privacy) concerns",
    r"\bi am (programmed|designed|instructed) (not to|to avoid|to refuse to) (provide|generate|share|discuss|assist with) (that|this|such) (content|information|material|request|topic|subject)",

    # NSFW and illegal content refusals
    r"\bi cannot (generate|provide|share|discuss) (nsfw|explicit|sexual|adult|violent|illegal|dangerous|harmful|private|personal) (content|material|information|stories|requests|topics)",
    r"\bi do not (support|condone|promote|encourage|endorse) (illegal|dangerous|harmful|unethical|explicit|adult) (activities|behavior|content|material|requests)",
    r"\bfor your safety,? i cannot (provide|generate|share|discuss) (that|this|such) (content|information|material|request|topic|subject)",
    r"\bi cannot provide (medical|legal|financial) advice or (diagnoses|services|recommendations)",
    r"\bi am not a (doctor|lawyer|financial advisor|therapist) and cannot (give|provide|offer) (advice|diagnosis|services|recommendations)",

    # Privacy and personal info refusals
    r"\bi cannot provide (personal|private|confidential|sensitive) (information|details|data) about (myself|others|anyone)",
    r"\bi do not have access to (personal|private|confidential|sensitive) (information|details|data)",
    r"\bi cannot help with (hacking|bypassing security|illegal activities|breaking the law)",

    # Subtle/indirect refusals
    r"\bi'?m sorry,? but that'?s (not something i can do|outside my capabilities|beyond my abilities)",
    r"\bi'?m sorry,? but i must decline",
    r"\bi'?m sorry,? but i cannot comply with that request",
    r"\bi'?m sorry,? but i cannot fulfill that request",
    r"\bi'?m sorry,? but i am not able to assist with that",
    r"\bi'?m sorry,? but i am not able to provide that information",
    r"\bi'?m sorry,? but i am not able to generate that content",
    r"\bi'?m sorry,? but i am not able to help with that",
    r"\bi'?m sorry,? but i am not able to create that",
    r"\bi'?m sorry,? but i am not able to discuss that topic",
    r"\bi'?m sorry,? but i am not able to share that",
    r"\bi'?m sorry,? but i am not able to do that",

    # "As an AI" disclaimers (common in refusals)
    r"\bas an (ai|language model|artificial intelligence),? (i cannot|i am not able to|i am not permitted to|i am not allowed to|i do not|i cannot|i'm unable to|i can't)",

    # Policy reference
    r"\bthis request (violates|is against|contravenes) (my|company|content) (guidelines|policies|rules|terms of service)",
    r"\bi am required to follow (guidelines|policies|rules|terms of service)",
    r"\bi must adhere to (guidelines|policies|rules|terms of service)",
]


def call_openrouter_api_sync(
    system_prompt: dict = None,
    messages: Union[dict, List[dict]] = None,
    llm_model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
    top_p: float = DEFAULT_TOP_P,
    frequency_penalty: float = DEFAULT_FREQUENCY_PENALTY,
    presence_penalty: float = DEFAULT_PRESENCE_PENALTY,
    max_retries: int = 4,
    max_response_attempts: int = 4,
) -> str:
    """
    Synchronous version of OpenRouter API call with retry logic and refusal detection.

    Args:
        system_prompt: System message dict with role and content
        messages: User messages (dict or list of dicts)
        llm_model: Model to use (default: gpt-4o-mini)
        max_tokens: Maximum response length
        temperature: Randomness (0.0-2.0)
        top_p: Nucleus sampling (0.0-1.0)
        frequency_penalty: Reduce repetition (0.0-2.0)
        presence_penalty: Encourage new topics (0.0-2.0)
        max_retries: API retry attempts
        max_response_attempts: Refusal retry attempts

    Returns:
        AI response string or error message
    """

    # Normalize messages to list
    if messages is None:
        messages = []
    elif isinstance(messages, dict):
        messages = [messages]

    # Prepend system prompt if given
    full_messages = []
    if system_prompt:
        full_messages.append(system_prompt)
    full_messages.extend(messages)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    for api_attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json={
                    "model": llm_model,
                    "messages": full_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                }
            )

            if response.status_code == 200:
                data = response.json()

                for response_attempt in range(max_response_attempts):
                    content = data["choices"][0]["message"]["content"]

                    if not is_refusal_response(content):
                        return content

                    print(f"⚠️ Refusal detected (attempt {response_attempt+1}/{max_response_attempts}), retrying...")

                    # Modify last user message to encourage retry
                    if full_messages:
                        full_messages[-1]["content"] += " (please try again, be more creative)"

                    # Retry with modified prompt
                    retry_response = requests.post(
                        OPENROUTER_API_URL,
                        headers=headers,
                        json={
                            "model": llm_model,
                            "messages": full_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "top_p": top_p,
                            "frequency_penalty": frequency_penalty,
                            "presence_penalty": presence_penalty,
                        }
                    )

                    if retry_response.status_code == 200:
                        data = retry_response.json()
                        content = data["choices"][0]["message"]["content"]
                    else:
                        break

                return content

            elif response.status_code == 403:
                print(f"⚠️ 403 Forbidden (attempt {api_attempt}/{max_retries}), retrying...")
                time.sleep(1)
                continue
            else:
                error_msg = f"⚠️ Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    pass
                return error_msg

        except Exception as e:
            print(f"⚠️ Request failed (attempt {api_attempt}/{max_retries}): {str(e)}")
            if api_attempt < max_retries:
                time.sleep(1)
                continue
            return f"⚠️ Error: {str(e)}"

    return "⚠️ Error: API retries exhausted"


def is_refusal_response(response: str) -> bool:
    """
    Check if the AI response contains refusal patterns.

    Args:
        response: AI response text

    Returns:
        True if refusal detected, False otherwise
    """
    response_lower = response.lower()
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, response_lower):
            return True
    return False


def generate_compliance_analysis_sync(product: str, country: str) -> str:
    """
    Synchronous version: Generate compliance analysis for a product in a specific country.

    Args:
        product: Product description
        country: Target country/region

    Returns:
        Compliance analysis string
    """
    system_prompt = {
        "role": "system",
        "content": "You are a compliance expert specializing in product regulations. Provide detailed, actionable compliance requirements for products entering different markets. Focus on safety standards, labeling requirements, certifications, and import documentation."
    }

    user_message = {
        "role": "user",
        "content": f"Analyze compliance requirements for this product: '{product}' being sold in {country}. Provide specific standards, certifications, and regulatory requirements."
    }

    return call_openrouter_api_sync(
        system_prompt=system_prompt,
        messages=user_message,
        temperature=0.3,  # Lower temperature for more factual responses
        max_tokens=512
    )