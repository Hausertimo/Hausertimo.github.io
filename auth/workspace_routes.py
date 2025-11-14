"""
Workspace CRUD operations and page routes
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from .client import supabase
from .decorators import require_auth
from .utils import get_current_user_id, check_workspace_limit
from .exceptions import LimitExceededError


# Create Blueprint for workspace API routes
workspace_bp = Blueprint('supabase_workspace', __name__, url_prefix='/api/workspaces')

# Create Blueprint for page routes (no prefix)
pages_bp = Blueprint('pages', __name__)


# ============================================================================
# PAGE ROUTES (HTML Pages)
# ============================================================================

@pages_bp.route('/dashboard')
@require_auth
def dashboard_page():
    """Serve the dashboard page"""
    return render_template('dashboard.html')


@pages_bp.route('/workspace/<workspace_id>')
@require_auth
def workspace_page(workspace_id):
    """Serve the workspace view page"""
    return render_template('workspace_view.html')


# ============================================================================
# WORKSPACE API ROUTES
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

        # Get next workspace number for this user (MAX + 1, not count + 1)
        # This prevents duplicate numbers if workspaces are archived
        max_number_result = supabase.table('workspaces') \
            .select('workspace_number') \
            .eq('user_id', user_id) \
            .order('workspace_number', desc=True) \
            .limit(1) \
            .execute()

        workspace_number = 1
        if max_number_result.data and len(max_number_result.data) > 0:
            workspace_number = max_number_result.data[0]['workspace_number'] + 1

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
