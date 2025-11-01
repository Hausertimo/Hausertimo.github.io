"""
Main routes for static pages and resources
"""

from flask import Blueprint, send_file, send_from_directory

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def serve_index():
    """Serve the main landing page"""
    return send_file('static/index.html')


@main_bp.route("/privacy")
def serve_privacy():
    """Serve the privacy policy page"""
    return send_file('static/privacy.html')


@main_bp.route("/terms")
def serve_terms():
    """Serve the terms of service page"""
    return send_file('static/terms.html')


@main_bp.route("/contact")
def serve_contact():
    """Serve the contact page"""
    return send_file('static/contact.html')


@main_bp.route("/img/<path:filename>")
def serve_image(filename):
    """Serve images from the img directory for email signatures"""
    return send_from_directory('img', filename)
