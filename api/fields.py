"""
Field Framework API endpoints
Handles dynamic field blocks for the NormScout application
"""

from flask import Blueprint, jsonify, request
from .field_framework import FieldRenderer
import json
import logging

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