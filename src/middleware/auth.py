from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.services.auth import verify_token
from src.utils import error_response


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes"""

    EXCLUDED_PATHS = ["/", "/api/auth/login"]

    async def dispatch(self, request: Request, call_next):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response(
                    message="Missing or invalid authorization header", code=401
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]

        try:
            user = await verify_token(token)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=error_response(message=str(e), code=401),
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Store user in request state
        request.state.user = user

        return await call_next(request)
