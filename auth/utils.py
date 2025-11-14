"""
Helper functions for user management and limit checking
"""

from typing import Dict, Any
from flask import request
from .client import supabase
from .config import Config
from .exceptions import LimitExceededError


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
