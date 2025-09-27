"""
OpenRouter API integration
Generic API client for making OpenRouter calls
"""

import requests
import json
import logging
import os

logger = logging.getLogger(__name__)

# OpenRouter API settings
OPENROUTER_API_KEY = os.environ.get("openrouter")
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# Log API key status on module load
if OPENROUTER_API_KEY:
    logger.info(f"✓ OpenRouter API key found (length: {len(OPENROUTER_API_KEY)} chars)")
else:
    logger.error("✗ OpenRouter API key NOT FOUND! Set 'openrouter' environment variable.")


def call_openrouter(messages: list, model: str = "openai/gpt-4o-mini",
                    temperature: float = 0.3, max_tokens: int = 512) -> dict:
    """
    Generic OpenRouter API call

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (default: gpt-4o-mini)
        temperature: Response randomness (0-1)
        max_tokens: Max response length

    Returns:
        Dict with either:
        - {"success": True, "content": "response text"}
        - {"success": False, "error": "error message"}
    """
    if not OPENROUTER_API_KEY:
        return {
            "success": False,
            "error": "OpenRouter API key not configured"
        }

    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://normscout.fly.dev",
            "X-Title": "NormScout",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        logger.info(f"Calling OpenRouter API with model: {model}")

        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.info(f"API call successful, response length: {len(content)} chars")
                return {
                    "success": True,
                    "content": content
                }
            else:
                return {
                    "success": False,
                    "error": "Unexpected API response structure"
                }
        else:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_msg = error_json.get('error', {}).get('message', error_msg)
            except:
                pass

            logger.error(f"OpenRouter API error: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out after 30 seconds"
        }
    except Exception as e:
        logger.exception(f"Exception calling OpenRouter API: {str(e)}")
        return {
            "success": False,
            "error": f"API call failed: {str(e)}"
        }


def analyze_product_compliance(product: str, country: str) -> dict:
    """
    Analyze compliance requirements for a product in a specific country
    This is a specific use case of the generic call_openrouter function

    Args:
        product: Product description
        country: Country code (e.g., 'us', 'eu', 'uk')

    Returns:
        Dictionary with analysis result, status, and metadata
    """
    logger.info(f"Analyzing compliance for product: {product}, country: {country}")

    # Country mapping for better AI responses
    country_names = {
        'us': 'United States',
        'eu': 'European Union',
        'uk': 'United Kingdom',
        'ca': 'Canada',
        'au': 'Australia',
        'jp': 'Japan',
        'ch': 'Switzerland'
    }

    country_full_name = country_names.get(country, country)

    # Build messages for compliance analysis
    messages = [
        {
            "role": "system",
            "content": "You are a compliance expert specializing in product regulations. Provide detailed, actionable compliance requirements for products entering different markets. Focus on safety standards, labeling requirements, certifications, and import documentation."
        },
        {
            "role": "user",
            "content": f"Analyze compliance requirements for this product: '{product}' being sold in {country_full_name}. Provide specific standards, certifications, and regulatory requirements."
        }
    ]

    # Call the generic OpenRouter function
    result = call_openrouter(messages)

    if result["success"]:
        return {
            "result": result["content"],
            "product": product,
            "country": country_full_name,
            "status": "success"
        }
    else:
        return {
            "result": f"Error: {result['error']}",
            "product": product,
            "country": country_full_name,
            "status": "error",
            "error": result["error"]
        }