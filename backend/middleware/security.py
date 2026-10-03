"""
Birthday Quest - Security Middleware

Request-level security checks.
"""

from __future__ import annotations

from flask import Flask, request

from utils.responses import error_response


# ------------------------------------------------------------
# HOST VALIDATION
# ------------------------------------------------------------

def register_security_middleware(app: Flask) -> None:
    """
    Register request-level security checks.
    """

    @app.before_request
    def validate_request_host():
        """
        Validate the incoming Host header against the configured
        trusted host list.

        During local development, localhost and 127.0.0.1 are
        allowed by default.
        """

        trusted_hosts = app.config.get(
            "TRUSTED_HOSTS",
            [],
        )

        # If no trusted hosts are configured, do not perform
        # host validation here.
        if not trusted_hosts:
            return None

        host = request.host.split(":", 1)[0].lower()

        normalized_hosts = {
            trusted_host.lower().strip()
            for trusted_host in trusted_hosts
            if trusted_host.strip()
        }

        if host not in normalized_hosts:
            return error_response(
                code="INVALID_HOST",
                message="The requested host is not allowed.",
                status_code=400,
            )

        return None
