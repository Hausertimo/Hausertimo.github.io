"""
Custom exceptions for authentication and workspace management
"""


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
