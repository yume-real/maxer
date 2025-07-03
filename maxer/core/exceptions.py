from typing import Any


class MaxerException(Exception):
    """Base exception for Maxer."""
    pass


class MaxerHTTPException(MaxerException):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"HTTP {status_code}: {body[:200]}")
        self.status_code = status_code
        self.body = body


class MaxerNetworkException(MaxerException):
    pass


class MaxerValidationException(MaxerException):
    pass


class MaxerAPIError(MaxerHTTPException):
    def __init__(self, status_code: int, error: dict[str, Any]):
        self.code = error.get("code")
        self.description = error.get("description") or error.get("message")
        self.extra = {k: v for k, v in error.items() if k not in {"code", "description", "message"}}
        super().__init__(status_code, self.description or str(error)) 