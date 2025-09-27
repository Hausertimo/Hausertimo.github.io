"""
OpenRouter API integration for compliance analysis
Handles all AI-powered compliance requirement analysis
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
    logger.info(f"  Key starts with: {OPENROUTER_API_KEY[:10]}..." if len(OPENROUTER_API_KEY) > 10 else "  Key is very short!")
else:
    logger.error("✗ OpenRouter API key NOT FOUND! Set 'openrouter' environment variable.")
    logger.error("  On Fly.io, use: fly secrets set openrouter='your-api-key-here'")
    logger.error("  Locally, use: export openrouter='your-api-key-here'")


def analyze_product_compliance(product: str, country: str) -> dict:
    """
    Analyze compliance requirements for a product in a specific country

    Args:
        product: Product description
        country: Country code (e.g., 'us', 'eu', 'uk')

    Returns:
        Dictionary with analysis result, status, and metadata
    """
    logger.info("=== API Request Received ===")
    logger.info(f"Product: {product}")
    logger.info(f"Country: {country}")

    # Check API key first
    if not OPENROUTER_API_KEY:
        logger.error("API key is missing - cannot process request")
        return {
            "result": "Configuration error: OpenRouter API key not configured. Please contact administrator.",
            "status": "error",
            "error": "Missing API key"
        }

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

    # Call OpenRouter API directly
    try:
        # CRITICAL: OpenRouter requires these headers!
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://normscout.fly.dev",  # YOUR SITE URL - REQUIRED!
            "X-Title": "NormScout",  # YOUR APP NAME - REQUIRED!
            "Content-Type": "application/json"
        }

        logger.info("Headers configured (API key hidden)")
        logger.info(f"  HTTP-Referer: {headers['HTTP-Referer']}")
        logger.info(f"  X-Title: {headers['X-Title']}")

        # System prompt and user message
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

        # API request payload
        payload = {
            "model": "openai/gpt-4o-mini",  # Using cheap, fast model
            "messages": messages,
            "temperature": 0.3,  # Lower = more factual
            "max_tokens": 512
        }

        logger.info(f"Calling OpenRouter API...")
        logger.info(f"  Model: {payload['model']}")
        logger.info(f"  Product: {product}, Country: {country_full_name}")

        # Make the API call with timeout
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30  # 30 second timeout
        )

        logger.info(f"API Response Status: {response.status_code}")

        # Log response headers for debugging
        if response.status_code != 200:
            logger.error(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            logger.info("API call successful!")

            # Check if response has expected structure
            if 'choices' in result and len(result['choices']) > 0:
                ai_content = result['choices'][0]['message']['content']
                logger.info(f"Response length: {len(ai_content)} chars")
            else:
                logger.error(f"Unexpected API response structure: {result}")
                ai_content = "Received unexpected response format from API"

            return {
                "result": ai_content,
                "product": product,
                "country": country_full_name,
                "status": "success"
            }
        else:
            # Log the full error for debugging
            error_detail = f"Status {response.status_code}: {response.text}"
            logger.error(f"OpenRouter API Error: {error_detail}")

            # Parse error message if JSON
            try:
                error_json = response.json()
                if 'error' in error_json:
                    error_msg = error_json.get('error', {}).get('message', error_detail)
                    error_code = error_json.get('error', {}).get('code', 'unknown')
                    logger.error(f"Error code: {error_code}, Message: {error_msg}")

                    # Check for common issues
                    if 'invalid_api_key' in str(error_code):
                        error_detail = "Invalid API key. Please check your OpenRouter API key."
                    elif 'insufficient_quota' in str(error_code):
                        error_detail = "API quota exceeded. Please check your OpenRouter account."
            except:
                pass

            # Return error details to help debug
            return {
                "result": f"API Error: {error_detail}",
                "product": product,
                "country": country_full_name,
                "status": "error",
                "error": error_detail
            }

    except requests.exceptions.Timeout:
        logger.error("API request timed out after 30 seconds")
        return {
            "result": "Request timed out. Please try again.",
            "product": product,
            "country": country_full_name,
            "status": "timeout",
            "error": "Request timeout"
        }

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Exception calling API: {error_msg}")

        # Return fallback with error details
        return {
            "result": f"Error connecting to AI service: {error_msg}",
            "product": product,
            "country": country_full_name,
            "status": "exception",
            "error": error_msg
        }