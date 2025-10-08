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


def validate_product_input(product: str) -> bool:
    """
    Check if the input is deliberate garbage (not just weird products)
    Uses confidence scoring to be less aggressive
    Caches results in Redis for exact matches

    Args:
        product: User's input text

    Returns:
        True if valid/weird product, False only if definitely garbage
    """
    # Try to get cached validation result first
    try:
        import redis
        import os
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            cache_key = f"validation:{product}"
            cached = redis_client.get(cache_key)
            if cached is not None:
                logger.info(f"Cache hit for validation: '{product[:30]}...'")
                return cached == "true"
    except Exception as e:
        logger.warning(f"Cache check failed: {e}, proceeding without cache")
    messages = [
        {
            "role": "system",
            "content": """Rate if user is DESCRIBING A PRODUCT TO BUY/SELL vs just chatting.
Reply with ONLY a number between 0.0 and 1.0:
- 0.0-0.5: Describing a product/item for commerce
- 0.6-0.8: Unclear intent
- 0.9-1.0: NOT describing a product (personal feelings, chat, garbage)

Examples:
"wireless headphones" = 0.0 (product to sell)
"bluetooth speaker with bass" = 0.0 (product description)
"flying toilet paper" = 0.2 (weird product but still commerce)
"I love chicken" = 0.95 (personal preference, not selling chicken)
"I ate sandwich" = 0.95 (personal action, not product)
"chicken" = 0.3 (could be product)
"I love this" = 0.95 (emotion, not product)
"pretty much whatever" = 0.95 (vague chat)
"hello" = 0.9 (greeting)
"asdfgh" = 1.0 (garbage)

ONLY OUTPUT THE NUMBER, NOTHING ELSE."""
        },
        {
            "role": "user",
            "content": f"Rate this: '{product}'"
        }
    ]

    try:
        # Use Mistral 7B - very cheap and fast
        result = call_openrouter(
            messages,
            model="mistralai/mistral-7b-instruct",
            temperature=0.1,  # Low temperature for consistency
            max_tokens=3  # Just "0.9" or "1.0" - no room for extra text
        )

        if result["success"]:
            response = result["content"].strip()
            try:
                # Extract just the number (handle cases like "0.9 (explanation)")
                # Take only the first word/number
                number_part = response.split()[0] if response else ""
                # Remove any trailing punctuation
                number_part = number_part.rstrip('.,;:()')

                confidence = float(number_part)
                logger.info(f"Garbage confidence for '{product[:30]}...': {confidence}")

                # Only reject if VERY confident it's garbage (0.9 or higher)
                result = False if confidence >= 0.9 else True

                # Cache the result for 24 hours
                try:
                    if redis_url:
                        cache_key = f"validation:{product}"
                        redis_client.setex(cache_key, 86400, "true" if result else "false")  # 24 hour TTL
                        logger.info(f"Cached validation result for '{product[:30]}...'")
                except Exception as e:
                    logger.warning(f"Failed to cache validation: {e}")

                return result

            except (ValueError, IndexError):
                # Couldn't parse number, allow through
                logger.warning(f"Could not parse confidence: '{response}', allowing through")
                return True

    except Exception as e:
        logger.warning(f"Product validation error: {e}, allowing through")

    # Default to true if anything fails (don't block users)
    return True


def analyze_product_compliance(product: str, country: str) -> dict:
    """
    Analyze compliance requirements for a product in a specific country
    This is a specific use case of the generic call_openrouter function
    Caches results in Redis for exact product+country matches

    Args:
        product: Product description
        country: Country code (e.g., 'us', 'eu', 'uk')

    Returns:
        Dictionary with analysis result, status, and metadata
    """
    logger.info(f"Analyzing compliance for product: {product}, country: {country}")

    # Try to get cached compliance result first
    try:
        import redis
        import os
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            cache_key = f"compliance:{product}:{country}"
            cached = redis_client.get(cache_key)
            if cached is not None:
                logger.info(f"Cache hit for compliance: '{product[:30]}...' in {country}")
                import json
                return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache check failed: {e}, proceeding without cache")

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
        response_dict = {
            "result": result["content"],
            "product": product,
            "country": country_full_name,
            "status": "success"
        }

        # Cache the successful result for 7 days
        try:
            if redis_url:
                cache_key = f"compliance:{product}:{country}"
                import json
                redis_client.setex(cache_key, 604800, json.dumps(response_dict))  # 7 day TTL
                logger.info(f"Cached compliance result for '{product[:30]}...' in {country}")
        except Exception as e:
            logger.warning(f"Failed to cache compliance: {e}")

        return response_dict
    else:
        return {
            "result": f"Error: {result['error']}",
            "product": product,
            "country": country_full_name,
            "status": "error",
            "error": result["error"]
        }