from typing import Optional, Any


def success_response(data: Optional[Any] = None, message: str = "Success") -> dict:
    """Create a successful response"""
    return {"code": 200, "message": message, "data": data}


def error_response(
    message: str = "Error", code: int = 400, data: Optional[Any] = None
) -> dict:
    """Create an error response"""
    return {"code": code, "message": message, "data": data}
