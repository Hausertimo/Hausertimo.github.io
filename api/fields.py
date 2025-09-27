"""
Field Framework API endpoints
Handles dynamic field blocks for the NormScout application
"""

from flask import Blueprint, jsonify, request
from .field_framework import FieldRenderer
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Create Blueprint for field-related routes
field_bp = Blueprint('fields', __name__)

# Store the renderer instance
field_renderer = None


@field_bp.route("/api/fields/get", methods=["GET"])
def get_fields():
    """Get field blocks to display"""
    global field_renderer

    if field_renderer and field_renderer.blocks:
        return jsonify({
            "status": "success",
            "blocks": field_renderer.render_all_blocks()
        })
    else:
        return jsonify({
            "status": "success",
            "blocks": []
        })


@field_bp.route("/api/fields/submit", methods=["POST"])
def submit_field_data():
    """Receive submitted field data"""
    data = request.get_json()
    block_id = data.get("block_id")
    fields = data.get("fields")

    logger.info(f"Received field data for block: {block_id}")
    logger.info(f"Fields: {json.dumps(fields, indent=2)}")

    # You can process the data here however you want
    # For now, just acknowledge receipt

    return jsonify({
        "status": "success",
        "message": f"Received data for block: {block_id}",
        "received_fields": fields
    })


@field_bp.route("/api/feedback/submit", methods=["POST"])
def submit_feedback():
    """Save user feedback to a file"""
    data = request.get_json()

    # Create feedback directory if it doesn't exist
    feedback_dir = "feedback"
    if not os.path.exists(feedback_dir):
        os.makedirs(feedback_dir)

    # Save to JSON Lines file (one JSON object per line)
    feedback_file = os.path.join(feedback_dir, "feedback.jsonl")

    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "name": data.get("name"),
        "email": data.get("email"),
        "product": data.get("product"),
        "message": data.get("message")
    }

    try:
        with open(feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_entry) + "\n")

        logger.info(f"Feedback saved from {data.get('email', 'unknown')}")

        return jsonify({
            "status": "success",
            "message": "Thank you for your feedback! We'll review it shortly."
        })

    except Exception as e:
        logger.error(f"Failed to save feedback: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to save feedback. Please try again."
        }), 500