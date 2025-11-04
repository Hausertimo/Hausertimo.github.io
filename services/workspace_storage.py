"""
Workspace storage using Redis for persistent product compliance workspaces
"""
import json
import uuid
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def create_workspace(redis_client, session_data: dict) -> str:
    """
    Convert a session to a persistent workspace

    Args:
        redis_client: Redis client instance
        session_data: Session dictionary from conversation_sessions

    Returns:
        workspace_id: UUID string for the new workspace
    """
    workspace_id = str(uuid.uuid4())

    workspace = {
        "id": workspace_id,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        "product": {
            "description": session_data.get("product_description", ""),
            "conversation_history": session_data.get("history", [])
        },
        "analysis": {
            "matched_norms": session_data.get("matched_norms", []),
            "all_results": session_data.get("all_norm_results", []),
            "analyzed_at": session_data.get("analyzed"),
            "total_matched": len(session_data.get("matched_norms", []))
        },
        "qa_history": session_data.get("qa_history", []),
        "metadata": {
            "status": "analyzed",
            "version": 1,
            "session_id": session_data.get("session_id", "")
        }
    }

    # Store in Redis with 30-day expiration (2592000 seconds)
    try:
        redis_client.setex(
            f"workspace:{workspace_id}",
            2592000,  # 30 days
            json.dumps(workspace)
        )
        logger.info(f"Created workspace {workspace_id}")
        return workspace_id
    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise


def load_workspace(redis_client, workspace_id: str) -> Optional[dict]:
    """
    Load workspace from Redis

    Args:
        redis_client: Redis client instance
        workspace_id: UUID string for the workspace

    Returns:
        workspace data dict or None if not found
    """
    try:
        data = redis_client.get(f"workspace:{workspace_id}")
        if not data:
            logger.warning(f"Workspace {workspace_id} not found")
            return None

        workspace = json.loads(data)
        logger.info(f"Loaded workspace {workspace_id}")
        return workspace
    except Exception as e:
        logger.error(f"Failed to load workspace {workspace_id}: {e}")
        return None


def update_workspace(redis_client, workspace_id: str, updates: dict) -> bool:
    """
    Update workspace data

    Args:
        redis_client: Redis client instance
        workspace_id: UUID string for the workspace
        updates: Dictionary of fields to update

    Returns:
        True if successful, False otherwise
    """
    try:
        workspace = load_workspace(redis_client, workspace_id)
        if not workspace:
            return False

        # Merge updates
        workspace.update(updates)
        workspace["updated"] = datetime.now().isoformat()

        # Save back to Redis
        redis_client.setex(
            f"workspace:{workspace_id}",
            2592000,  # Reset 30-day expiration
            json.dumps(workspace)
        )

        logger.info(f"Updated workspace {workspace_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update workspace {workspace_id}: {e}")
        return False


def delete_workspace(redis_client, workspace_id: str) -> bool:
    """
    Delete a workspace

    Args:
        redis_client: Redis client instance
        workspace_id: UUID string for the workspace

    Returns:
        True if successful, False otherwise
    """
    try:
        result = redis_client.delete(f"workspace:{workspace_id}")
        if result:
            logger.info(f"Deleted workspace {workspace_id}")
            return True
        else:
            logger.warning(f"Workspace {workspace_id} not found for deletion")
            return False
    except Exception as e:
        logger.error(f"Failed to delete workspace {workspace_id}: {e}")
        return False


def list_workspaces(redis_client, pattern: str = "workspace:*") -> list:
    """
    List all workspace IDs (for admin/debugging purposes)

    Args:
        redis_client: Redis client instance
        pattern: Redis key pattern to match

    Returns:
        List of workspace IDs
    """
    try:
        keys = redis_client.keys(pattern)
        workspace_ids = [key.decode('utf-8').replace('workspace:', '') for key in keys]
        return workspace_ids
    except Exception as e:
        logger.error(f"Failed to list workspaces: {e}")
        return []
