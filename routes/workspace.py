"""
Workspace routes - persistent product compliance workspaces
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import logging
from datetime import datetime

from services.workspace_storage import (
    create_workspace,
    load_workspace,
    update_workspace,
    delete_workspace
)
from services.product_conversation import answer_analysis_question
from services.norm_matcher import match_norms

logger = logging.getLogger(__name__)

workspace_bp = Blueprint('workspace', __name__)


@workspace_bp.route('/workspace/<workspace_id>')
def workspace_page(workspace_id):
    """
    Render workspace page

    Args:
        workspace_id: UUID string for the workspace

    Returns:
        Rendered workspace template or 404
    """
    from app import redis_client  # Import here to avoid circular import

    workspace = load_workspace(redis_client, workspace_id)

    if not workspace:
        return render_template('error.html',
                             error="Workspace not found",
                             message="This workspace doesn't exist or has expired."), 404

    return render_template('workspace.html', workspace=workspace)


@workspace_bp.route('/api/workspace/create', methods=['POST'])
def api_create_workspace():
    """
    Create a new workspace from a session

    Expects:
        {"session_id": "uuid"}  (from conversation_sessions)

    Returns:
        {"workspace_id": "uuid", "url": "/workspace/uuid"}
    """
    from app import redis_client
    from routes.develope import conversation_sessions  # Import session store

    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id or session_id not in conversation_sessions:
            return jsonify({"error": "Invalid or expired session"}), 400

        session_data = conversation_sessions[session_id]

        # Check if analysis has been completed
        if not session_data.get('analyzed'):
            return jsonify({"error": "Please complete the analysis first"}), 400

        # Create workspace
        workspace_id = create_workspace(redis_client, session_data)

        return jsonify({
            "workspace_id": workspace_id,
            "url": f"/workspace/{workspace_id}"
        })

    except Exception as e:
        logger.exception(f"Error creating workspace: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_bp.route('/api/workspace/<workspace_id>/data', methods=['GET'])
def api_get_workspace_data(workspace_id):
    """
    Get workspace data as JSON

    Args:
        workspace_id: UUID string

    Returns:
        Workspace data dictionary
    """
    from app import redis_client

    workspace = load_workspace(redis_client, workspace_id)

    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    return jsonify(workspace)


@workspace_bp.route('/api/workspace/<workspace_id>/ask', methods=['POST'])
def api_workspace_ask(workspace_id):
    """
    Ask questions about workspace analysis

    Expects:
        {"question": "..."}

    Returns:
        {"answer": "...", "relevant_norms": [...]}
    """
    from app import redis_client

    try:
        workspace = load_workspace(redis_client, workspace_id)

        if not workspace:
            return jsonify({"error": "Workspace not found"}), 404

        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Get analysis data
        product_description = workspace['product']['description']
        matched_norms = workspace['analysis']['matched_norms']
        all_norm_results = workspace['analysis']['all_results']
        qa_history = workspace.get('qa_history', [])

        # Call Q&A function with chat history for context
        result = answer_analysis_question(
            product_description=product_description,
            matched_norms=matched_norms,
            all_norms=all_norm_results,
            question=question,
            qa_history=qa_history
        )

        # Store Q&A in workspace history
        if 'qa_history' not in workspace:
            workspace['qa_history'] = []

        workspace['qa_history'].append({
            "question": question,
            "answer": result["answer"],
            "timestamp": datetime.now().isoformat()
        })

        # Update workspace
        update_workspace(redis_client, workspace_id, workspace)

        logger.info(f"Q&A for workspace {workspace_id}: question_length={len(question)}")

        return jsonify(result)

    except Exception as e:
        logger.exception(f"Error in workspace Q&A: {e}")
        return jsonify({"error": str(e)}), 500


@workspace_bp.route('/api/workspaces/<workspace_id>/reanalyze', methods=['POST'])
def api_workspace_reanalyze(workspace_id):
    """
    Re-run compliance analysis for a workspace after product description changes

    Returns:
        {"matched_norms": [...], "analysis": {...}}
    """
    from app import redis_client

    try:
        workspace = load_workspace(redis_client, workspace_id)

        if not workspace:
            return jsonify({"error": "Workspace not found"}), 404

        # Get current product description
        product_description = workspace['product']['description']

        logger.info(f"Re-analyzing workspace {workspace_id}")

        # Run norm matching analysis - collect all results
        from services.norm_matcher import match_norms_streaming

        matched_norms = []
        all_results = []

        # Consume the streaming generator to get final results
        for event in match_norms_streaming(product_description, max_workers=10):
            if event[0] == 'complete':
                matched_norms = event[1]  # matched_results
                all_results = event[2]     # all_results including rejected
                break

        # Update workspace with new analysis
        workspace['analysis'] = {
            'matched_norms': matched_norms,
            'all_results': all_results,  # Now includes rejected norms for Q&A
            'analyzed_at': datetime.now().isoformat()
        }

        # Save updated workspace
        update_workspace(redis_client, workspace_id, workspace)

        logger.info(f"Re-analysis complete for workspace {workspace_id}: {len(matched_norms)} matched, {len(all_results)} total")

        return jsonify({
            "matched_norms": matched_norms,
            "analysis": workspace['analysis'],
            "success": True
        })

    except Exception as e:
        logger.exception(f"Error re-analyzing workspace: {e}")
        return jsonify({"error": "Failed to re-analyze product. Please try again.", "success": False}), 500


@workspace_bp.route('/api/workspace/<workspace_id>/delete', methods=['DELETE'])
def api_delete_workspace(workspace_id):
    """
    Delete a workspace

    Args:
        workspace_id: UUID string

    Returns:
        {"success": true}
    """
    from app import redis_client

    try:
        success = delete_workspace(redis_client, workspace_id)

        if not success:
            return jsonify({"error": "Workspace not found"}), 404

        return jsonify({"success": True})

    except Exception as e:
        logger.exception(f"Error deleting workspace: {e}")
        return jsonify({"error": str(e)}), 500
