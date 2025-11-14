"""
Q&A functionality for workspaces
"""

from datetime import datetime
from flask import request, jsonify
from .client import supabase
from .decorators import require_auth
from .utils import get_current_user_id, check_qa_limit
from .exceptions import LimitExceededError
from .workspace_routes import workspace_bp


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
