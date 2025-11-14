"""
OAuth authentication routes (Google, GitHub, Apple)
"""

from flask import (
    Blueprint, request, jsonify, redirect, session,
    make_response, render_template_string
)
from .client import supabase
from .config import Config
from .decorators import require_auth
from .utils import get_current_user


# Create Blueprint for OAuth routes
auth_bp = Blueprint('supabase_auth', __name__, url_prefix='/auth')


@auth_bp.route('/login/<provider>')
def login(provider: str):
    """
    Initiate OAuth login flow

    Supported providers: google, github, apple
    """
    if provider not in ['google', 'github', 'apple']:
        return jsonify({"error": "Unsupported provider"}), 400

    try:
        # Get redirect URL from query params (for deep linking)
        redirect_to = request.args.get('redirect_to', f"{Config.SITE_URL}/dashboard")

        # Store redirect in session
        session['auth_redirect'] = redirect_to

        # Generate Supabase OAuth URL
        auth_response = supabase.auth.sign_in_with_oauth({
            "provider": provider,
            "options": {
                "redirect_to": f"{Config.SITE_URL}/auth/callback"
            }
        })

        # Redirect to provider's login page
        return redirect(auth_response.url)

    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500


@auth_bp.route('/callback')
def callback():
    """
    OAuth callback handler
    Supabase redirects here after user authenticates with provider
    """
    try:
        # Get authorization code from query parameters
        code = request.args.get('code')

        if not code:
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head><title>Login Failed</title></head>
                <body>
                    <h2>Login Failed</h2>
                    <p>No authorization code received from provider.</p>
                    <a href="/">Return to Home</a>
                </body>
                </html>
            """), 400

        # Exchange code for session with Supabase
        try:
            auth_response = supabase.auth.exchange_code_for_session({
                "auth_code": code
            })

            if not auth_response or not auth_response.session:
                raise Exception("No session received from Supabase")

            session = auth_response.session
            access_token = session.access_token
            refresh_token = session.refresh_token
            user = auth_response.user

        except Exception as e:
            print(f"ERROR: Code exchange failed: {e}")
            return render_template_string("""
                <!DOCTYPE html>
                <html>
                <head><title>Login Failed</title></head>
                <body>
                    <h2>Login Failed</h2>
                    <p>Failed to exchange authorization code: """ + str(e) + """</p>
                    <a href="/">Return to Home</a>
                </body>
                </html>
            """), 500

        # Return HTML that sets the cookie and redirects
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Logging in...</title>
        </head>
        <body>
            <p>Logging you in...</p>
            <script>
                // Send token to backend to set cookie
                fetch('/auth/session', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        access_token: '{access_token}',
                        refresh_token: '{refresh_token}'
                    }})
                }}).then(response => {{
                    if (response.ok) {{
                        window.location.href = '/dashboard';
                    }} else {{
                        document.body.innerHTML = '<p>Login failed. Could not create session.</p>';
                    }}
                }}).catch(err => {{
                    document.body.innerHTML = '<p>Login failed: ' + err + '</p>';
                }});
            </script>
        </body>
        </html>
        """

        return render_template_string(html)

    except Exception as e:
        print(f"ERROR: Callback failed: {e}")
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head><title>Login Failed</title></head>
            <body>
                <h2>Login Failed</h2>
                <p>An unexpected error occurred: """ + str(e) + """</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
        """), 500


@auth_bp.route('/session', methods=['POST'])
def create_session():
    """
    Create session after OAuth login
    Frontend sends access_token, backend sets httpOnly cookie
    """
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')

        if not access_token:
            return jsonify({"error": "No access token"}), 400

        # Verify token with Supabase
        user = supabase.auth.get_user(access_token)
        if not user or not user.user:
            return jsonify({"error": "Invalid token"}), 401

        # Set httpOnly cookie
        response = make_response(jsonify({
            "success": True,
            "user": {
                "id": user.user.id,
                "email": user.user.email,
                "user_metadata": user.user.user_metadata
            }
        }))

        response.set_cookie(
            Config.SESSION_COOKIE_NAME,
            access_token,
            httponly=Config.SESSION_COOKIE_HTTPONLY,
            secure=Config.SESSION_COOKIE_SECURE,
            samesite=Config.SESSION_COOKIE_SAMESITE,
            max_age=60 * 60 * 24 * 7  # 7 days
        )

        return response

    except Exception as e:
        return jsonify({"error": f"Session creation failed: {str(e)}"}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user - clear session cookie"""
    response = make_response(jsonify({"success": True}))
    response.set_cookie(Config.SESSION_COOKIE_NAME, '', expires=0)
    return response


@auth_bp.route('/me')
@require_auth
def get_current_user_info():
    """Get current user info"""
    user = get_current_user()
    return jsonify({
        "id": user.id,
        "email": user.email,
        "user_metadata": user.user_metadata,
        "created_at": user.created_at
    })
