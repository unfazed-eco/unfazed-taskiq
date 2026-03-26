class ResultIsMissingError(Exception):
    """Raised when task record is not found for task_id."""


class ResultNotReadyError(Exception):
    """Raised when task record exists but result is not ready (task still running)."""
