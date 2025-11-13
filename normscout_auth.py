"""
Supabase Authentication & Workspace Management Module
======================================================

Complete standalone module for:
- OAuth login (Google, GitHub, Apple)
- User management
- Workspace CRUD operations
- Q&A functionality
- PDF export

Ready to plug into Flask app!
"""

import os
import io
import json
from datetime import datetime
from functools import wraps
from typing import Optional, Dict, Any, List

from flask import (
    Blueprint, request, jsonify, redirect, session,
    make_response, send_file, render_template_string, url_for,
    send_from_directory
)
from supabase import create_client, Client

# WeasyPrint is optional - only needed for PDF export
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WARNING: WeasyPrint not available - PDF export will be disabled: {e}")
    print("         For local development, this is fine. For production, install GTK libraries.")

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration for Supabase and app limits"""

    # Supabase credentials (from environment variables)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

    # Workspace limits (None = unlimited, ready to enforce later)
    MAX_WORKSPACES_PER_USER = None  # Set to 50 when ready
    MAX_QA_PER_WORKSPACE = None     # Set to 100 when ready
    WARN_AT_WORKSPACE_COUNT = 45    # Show warning at 45/50
    WARN_AT_QA_COUNT = 90           # Show warning at 90/100

    # OAuth redirect URLs
    SITE_URL = os.getenv('SITE_URL', 'https://normscout.ch')

    # Session config
    SESSION_COOKIE_NAME = 'sb_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Only over HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'


# Initialize Supabase client
supabase: Client = create_client(
    Config.SUPABASE_URL,
    Config.SUPABASE_SERVICE_KEY
)

# Create Blueprint
auth_bp = Blueprint('supabase_auth', __name__, url_prefix='/auth')
workspace_bp = Blueprint('supabase_workspace', __name__, url_prefix='/api/workspaces')


# ============================================================================
# DATABASE SCHEMA (Run this SQL in Supabase SQL Editor)
# ============================================================================

"""
-- Users table is automatically created by Supabase Auth in auth.users

-- Workspaces table
CREATE TABLE IF NOT EXISTS public.workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- User-facing fields
    name TEXT NOT NULL,
    workspace_number INTEGER NOT NULL,

    -- Compliance data
    product_description TEXT NOT NULL,
    matched_norms JSONB,
    all_results JSONB,

    -- Q&A history
    qa_history JSONB DEFAULT '[]'::jsonb,
    qa_count INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Soft delete
    is_archived BOOLEAN DEFAULT FALSE,

    -- Constraints
    CONSTRAINT unique_workspace_number_per_user UNIQUE(user_id, workspace_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON workspaces(user_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_last_accessed ON workspaces(last_accessed DESC);
CREATE INDEX IF NOT EXISTS idx_workspaces_created_at ON workspaces(created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own workspaces
CREATE POLICY "Users can access own workspaces"
ON workspaces
FOR ALL
USING (auth.uid() = user_id);

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_workspaces_updated_at
    BEFORE UPDATE ON workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""


# ============================================================================
# EXCEPTIONS
# ============================================================================

class AuthError(Exception):
    """Base auth exception"""
    pass


class LimitExceededError(Exception):
    """Raised when user hits workspace or Q&A limits"""
    pass


class WorkspaceNotFoundError(Exception):
    """Raised when workspace doesn't exist"""
    pass


class UnauthorizedError(Exception):
    """Raised when user doesn't have permission"""
    pass


# ============================================================================
# AUTHENTICATION DECORATORS
# ============================================================================

def require_auth(f):
    """
    Decorator to protect routes - requires valid Supabase JWT token

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = get_current_user_id()
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header or cookie
        token = None

        # Try Authorization header first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')

        # Fall back to cookie
        if not token:
            token = request.cookies.get(Config.SESSION_COOKIE_NAME)

        if not token:
            return jsonify({"error": "Not authenticated"}), 401

        try:
            # Verify token with Supabase
            user = supabase.auth.get_user(token)
            if not user or not user.user:
                return jsonify({"error": "Invalid token"}), 401

            # Store user info in request context
            request.current_user = user.user

        except Exception as e:
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 401

        return f(*args, **kwargs)

    return decorated_function


def get_current_user_id() -> str:
    """Get current user ID from request context"""
    if hasattr(request, 'current_user'):
        return request.current_user.id
    return None


def get_current_user() -> Dict[str, Any]:
    """Get current user object from request context"""
    if hasattr(request, 'current_user'):
        return request.current_user
    return None


# ============================================================================
# LIMIT CHECKING (Ready but not enforced)
# ============================================================================

def check_workspace_limit(user_id: str) -> bool:
    """
    Check if user has reached workspace limit
    Returns True if under limit, raises LimitExceededError if over
    """
    if Config.MAX_WORKSPACES_PER_USER is None:
        return True  # Unlimited

    result = supabase.table('workspaces') \
        .select('id', count='exact') \
        .eq('user_id', user_id) \
        .eq('is_archived', False) \
        .execute()

    count = result.count if result.count else 0

    if count >= Config.MAX_WORKSPACES_PER_USER:
        raise LimitExceededError(
            f"You've reached the maximum of {Config.MAX_WORKSPACES_PER_USER} workspaces. "
            f"Delete some workspaces to create new ones."
        )

    return True


def check_qa_limit(workspace_id: str) -> bool:
    """
    Check if workspace has reached Q&A limit
    Returns True if under limit, raises LimitExceededError if over
    """
    if Config.MAX_QA_PER_WORKSPACE is None:
        return True  # Unlimited

    result = supabase.table('workspaces') \
        .select('qa_count') \
        .eq('id', workspace_id) \
        .single() \
        .execute()

    if not result.data:
        return True

    qa_count = result.data.get('qa_count', 0)

    if qa_count >= Config.MAX_QA_PER_WORKSPACE:
        raise LimitExceededError(
            f"This workspace has reached the maximum of {Config.MAX_QA_PER_WORKSPACE} questions. "
            f"Create a new workspace to continue."
        )

    return True


def get_workspace_count(user_id: str) -> int:
    """Get user's current workspace count"""
    result = supabase.table('workspaces') \
        .select('id', count='exact') \
        .eq('user_id', user_id) \
        .eq('is_archived', False) \
        .execute()

    return result.count if result.count else 0


# ============================================================================
# OAUTH ROUTES
# ============================================================================

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


# ============================================================================
# PAGE ROUTES (HTML Pages)
# ============================================================================

# Create a separate blueprint for pages (no /auth prefix)
pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/dashboard')
@require_auth
def dashboard_page():
    """Serve the dashboard page"""
    return send_from_directory('static', 'dashboard.html')


@pages_bp.route('/workspace/<workspace_id>')
@require_auth
def workspace_page(workspace_id):
    """Serve the workspace view page"""
    return send_from_directory('static', 'workspace_view.html')


# ============================================================================
# WORKSPACE ROUTES
# ============================================================================

@workspace_bp.route('/create', methods=['POST'])
@require_auth
def create_workspace():
    """
    Create a new workspace

    Request body:
    {
        "name": "IoT Thermostat Analysis",
        "product_description": "...",
        "matched_norms": [...],
        "all_results": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        # Check workspace limit
        check_workspace_limit(user_id)

        # Get next workspace number for this user
        workspace_count = get_workspace_count(user_id)
        workspace_number = workspace_count + 1

        # Create workspace
        workspace = {
            "user_id": user_id,
            "name": data.get('name'),
            "workspace_number": workspace_number,
            "product_description": data.get('product_description'),
            "matched_norms": data.get('matched_norms'),
            "all_results": data.get('all_results'),
            "qa_history": [],
            "qa_count": 0
        }

        result = supabase.table('workspaces').insert(workspace).execute()

        if not result.data:
            return jsonify({"error": "Failed to create workspace"}), 500

        return jsonify({
            "success": True,
            "workspace": result.data[0]
        }), 201

    except LimitExceededError as e:
        return jsonify({"error": str(e), "limit_exceeded": True}), 403

    except Exception as e:
        return jsonify({"error": f"Create failed: {str(e)}"}), 500


@workspace_bp.route('/', methods=['GET'])
@require_auth
def list_workspaces():
    """
    Get all workspaces for current user

    Query params:
    - sort_by: created_at | last_accessed | name (default: last_accessed)
    - order: asc | desc (default: desc)
    - archived: true | false (default: false)
    """
    try:
        user_id = get_current_user_id()

        # Get query params
        sort_by = request.args.get('sort_by', 'last_accessed')
        order = request.args.get('order', 'desc')
        show_archived = request.args.get('archived', 'false').lower() == 'true'

        # Build query
        query = supabase.table('workspaces') \
            .select('*') \
            .eq('user_id', user_id)

        if not show_archived:
            query = query.eq('is_archived', False)

        # Sort
        ascending = (order == 'asc')
        query = query.order(sort_by, desc=(not ascending))

        result = query.execute()

        return jsonify({
            "workspaces": result.data,
            "count": len(result.data)
        })

    except Exception as e:
        return jsonify({"error": f"List failed: {str(e)}"}), 500


@workspace_bp.route('/<workspace_id>', methods=['GET'])
@require_auth
def get_workspace(workspace_id: str):
    """Get single workspace by ID"""
    try:
        user_id = get_current_user_id()

        result = supabase.table('workspaces') \
            .select('*') \
            .eq('id', workspace_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        if not result.data:
            return jsonify({"error": "Workspace not found"}), 404

        # Update last_accessed
        supabase.table('workspaces') \
            .update({"last_accessed": datetime.utcnow().isoformat()}) \
            .eq('id', workspace_id) \
            .execute()

        return jsonify(result.data)

    except Exception as e:
        return jsonify({"error": f"Get failed: {str(e)}"}), 500


@workspace_bp.route('/<workspace_id>/rename', methods=['PATCH'])
@require_auth
def rename_workspace(workspace_id: str):
    """
    Rename a workspace

    Request body:
    {
        "name": "New Workspace Name"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        new_name = data.get('name')

        if not new_name:
            return jsonify({"error": "Name is required"}), 400

        # Update workspace
        result = supabase.table('workspaces') \
            .update({"name": new_name}) \
            .eq('id', workspace_id) \
            .eq('user_id', user_id) \
            .execute()

        if not result.data:
            return jsonify({"error": "Workspace not found or not authorized"}), 404

        return jsonify({
            "success": True,
            "workspace": result.data[0]
        })

    except Exception as e:
        return jsonify({"error": f"Rename failed: {str(e)}"}), 500


@workspace_bp.route('/<workspace_id>', methods=['DELETE'])
@require_auth
def delete_workspace(workspace_id: str):
    """
    Delete (archive) a workspace

    Query params:
    - permanent: true | false (default: false for soft delete)
    """
    try:
        user_id = get_current_user_id()
        permanent = request.args.get('permanent', 'false').lower() == 'true'

        if permanent:
            # Hard delete
            result = supabase.table('workspaces') \
                .delete() \
                .eq('id', workspace_id) \
                .eq('user_id', user_id) \
                .execute()
        else:
            # Soft delete (archive)
            result = supabase.table('workspaces') \
                .update({"is_archived": True}) \
                .eq('id', workspace_id) \
                .eq('user_id', user_id) \
                .execute()

        if not result.data:
            return jsonify({"error": "Workspace not found or not authorized"}), 404

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500


# ============================================================================
# Q&A ROUTES
# ============================================================================

@workspace_bp.route('/<workspace_id>/ask', methods=['POST'])
@require_auth
def ask_question(workspace_id: str):
    """
    Ask a question about the workspace

    Request body:
    {
        "question": "What certifications are needed?"
    }

    Note: This just saves the Q&A, you need to integrate with your LLM service
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        question = data.get('question')

        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Check Q&A limit
        check_qa_limit(workspace_id)

        # Get workspace
        workspace = supabase.table('workspaces') \
            .select('*') \
            .eq('id', workspace_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        if not workspace.data:
            return jsonify({"error": "Workspace not found"}), 404

        # TODO: Call your LLM service here with workspace context
        # For now, return placeholder
        answer = "[Your LLM integration goes here]"

        # Append Q&A to history
        qa_history = workspace.data.get('qa_history', [])
        qa_entry = {
            "question": question,
            "answer": answer,
            "timestamp": datetime.utcnow().isoformat()
        }
        qa_history.append(qa_entry)

        # Update workspace
        result = supabase.table('workspaces') \
            .update({
                "qa_history": qa_history,
                "qa_count": len(qa_history)
            }) \
            .eq('id', workspace_id) \
            .execute()

        return jsonify({
            "success": True,
            "qa": qa_entry
        })

    except LimitExceededError as e:
        return jsonify({"error": str(e), "limit_exceeded": True}), 403

    except Exception as e:
        return jsonify({"error": f"Ask failed: {str(e)}"}), 500


# ============================================================================
# PDF EXPORT
# ============================================================================

@workspace_bp.route('/<workspace_id>/export/pdf', methods=['GET'])
@require_auth
def export_workspace_pdf(workspace_id: str):
    """Export workspace as PDF"""
    # Check if WeasyPrint is available
    if not WEASYPRINT_AVAILABLE:
        return jsonify({
            "error": "PDF export is not available. WeasyPrint library is not installed.",
            "hint": "This feature requires GTK libraries. It may not work on Windows locally."
        }), 503

    try:
        user_id = get_current_user_id()

        # Get workspace
        workspace = supabase.table('workspaces') \
            .select('*') \
            .eq('id', workspace_id) \
            .eq('user_id', user_id) \
            .single() \
            .execute()

        if not workspace.data:
            return jsonify({"error": "Workspace not found"}), 404

        ws = workspace.data

        # Generate HTML for PDF
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 40px;
                }}
                h1 {{
                    color: #2563eb;
                    border-bottom: 3px solid #2563eb;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #1e40af;
                    margin-top: 30px;
                }}
                .meta {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .qa-item {{
                    margin: 20px 0;
                    padding: 15px;
                    background: #f3f4f6;
                    border-left: 4px solid #2563eb;
                }}
                .question {{
                    font-weight: bold;
                    color: #1e40af;
                }}
                .answer {{
                    margin-top: 10px;
                }}
                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    color: #6b7280;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <h1>NormScout Compliance Report</h1>
            <div class="meta">
                <strong>Workspace:</strong> {ws['name']}<br>
                <strong>Generated:</strong> {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}<br>
                <strong>Workspace #:</strong> {ws['workspace_number']}
            </div>

            <h2>Product Description</h2>
            <p>{ws['product_description']}</p>

            <h2>Compliance Results</h2>
            <p>{json.dumps(ws.get('matched_norms', []), indent=2)}</p>

            <h2>Question & Answer History</h2>
            {''.join([
                f'''
                <div class="qa-item">
                    <div class="question">Q: {qa['question']}</div>
                    <div class="answer">A: {qa['answer']}</div>
                </div>
                '''
                for qa in ws.get('qa_history', [])
            ]) or '<p>No questions asked yet.</p>'}

            <div class="footer">
                Generated by NormScout.ch
            </div>
        </body>
        </html>
        """

        # Convert to PDF
        if not WEASYPRINT_AVAILABLE:
            return jsonify({
                "error": "PDF export is not available in this environment. "
                        "WeasyPrint requires GTK libraries (Windows) or additional packages (Linux/Mac)."
            }), 503

        pdf = HTML(string=html_content).write_pdf()

        # Return as download
        return send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{ws['name'].replace(' ', '_')}.pdf"
        )

    except Exception as e:
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def register_blueprints(app):
    """Register all auth and workspace blueprints with Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(pages_bp)


def init_app(app):
    """Initialize Supabase auth with Flask app"""
    # Set secret key for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')

    # Register blueprints
    register_blueprints(app)

    print("OK: Supabase Auth module initialized")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

"""
# In your app.py:

from supabase_auth import init_app, require_auth, get_current_user_id

app = Flask(__name__)
init_app(app)  # This registers all auth routes

# Protected route example:
@app.route('/api/my-protected-route')
@require_auth
def my_route():
    user_id = get_current_user_id()
    return jsonify({"user_id": user_id})
"""
