from flask import Flask, request, jsonify, send_file
import asyncio
import os
from openrouter_api import generate_compliance_analysis

app = Flask(__name__)

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

    try:
        # Run the async AI analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ai_result = loop.run_until_complete(
            generate_compliance_analysis(product, country_full_name)
        )
        loop.close()

        return jsonify({
            "result": ai_result,
            "product": product,
            "country": country_full_name,
            "status": "success"
        })

    except Exception as e:
        # Fallback to simple response if AI fails
        fallback_result = f"Demo mode: Received product '{product}' for '{country_full_name}'. AI analysis temporarily unavailable."
        return jsonify({
            "result": fallback_result,
            "product": product,
            "country": country_full_name,
            "status": "fallback",
            "error": str(e)
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)