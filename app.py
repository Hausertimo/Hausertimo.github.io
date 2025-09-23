from flask import Flask, request, jsonify, send_file
import requests
import json
import os

app = Flask(__name__)

# OpenRouter API settings - all in one place, no config files
OPENROUTER_API_KEY = os.environ.get("openrouter")
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

@app.route("/")
def serve_index():
    return send_file('index.html')

@app.route("/style.css")
def serve_css():
    return send_file('style.css')

@app.route("/functions.js")
def serve_js():
    return send_file('functions.js')

@app.route("/api/run", methods=["POST"])
def run_python_code():
    data = request.get_json(force=True) or {}
    product = data.get("product", "")
    country = data.get("country", "")

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

    # Call OpenRouter API directly - simple and straightforward
    try:
        # CRITICAL: OpenRouter requires these headers!
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://normscout.fly.dev",  # YOUR SITE URL - REQUIRED!
            "X-Title": "NormScout",  # YOUR APP NAME - REQUIRED!
            "Content-Type": "application/json"
        }

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

        print(f"Calling OpenRouter API for product: {product}, country: {country_full_name}")

        # Make the API call
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)

        print(f"API Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            ai_content = result['choices'][0]['message']['content']

            return jsonify({
                "result": ai_content,
                "product": product,
                "country": country_full_name,
                "status": "success"
            })
        else:
            # Log the full error for debugging
            error_detail = f"Status {response.status_code}: {response.text}"
            print(f"OpenRouter API Error: {error_detail}")

            # Return error details to help debug
            return jsonify({
                "result": f"API Error: {error_detail}",
                "product": product,
                "country": country_full_name,
                "status": "error",
                "error": error_detail
            })

    except Exception as e:
        error_msg = str(e)
        print(f"Exception calling API: {error_msg}")

        # Return fallback with error details
        return jsonify({
            "result": f"Error connecting to AI service: {error_msg}",
            "product": product,
            "country": country_full_name,
            "status": "exception",
            "error": error_msg
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)