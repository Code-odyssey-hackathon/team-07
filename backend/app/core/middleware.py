"""
Madhyastha — Middleware
Request logging and error handling
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("madhyastha")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"→ {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            logger.info(
                f"← {request.method} {request.url.path} "
                f"[{response.status_code}] {duration:.3f}s"
            )
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"✗ {request.method} {request.url.path} "
                f"[ERROR] {duration:.3f}s — {str(e)}"
            )
            raise
