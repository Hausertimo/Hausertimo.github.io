"""
Main routes for static pages and resources
"""

from flask import Blueprint, send_file, send_from_directory, render_template, make_response

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def serve_index():
    """Serve the main landing page"""
    return render_template('index.html')


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


@main_bp.route("/investors")
def serve_investors():
    """Serve the investors page"""
    response = make_response(render_template('investors.html'))
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response


@main_bp.route("/img/<path:filename>")
def serve_image(filename):
    """Serve images from the img directory for email signatures"""
    return send_from_directory('static/img', filename)


# ==================== PAYMENT PAGES ====================

@main_bp.route("/payment/success")
def payment_success():
    """Serve the payment success page (redirect from Stripe)"""
    return send_file('static/payment_success.html')


@main_bp.route("/payment/cancel")
def payment_cancel():
    """Serve the payment cancelled page (redirect from Stripe)"""
    return send_file('static/payment_cancel.html')
