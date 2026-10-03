"""
Birthday Quest - Security Middleware

Request-level security checks.

Responsibilities:
- Validate the incoming Host header.
- Reject requests for untrusted hosts.
- Keep host validation centralized.
"""

from __future__ import annotations

from flask import Flask, request

from utils.responses import error_response


# ============================================================
# HOST VALIDATION
# ============================================================

def _get_normalized_trusted_hosts(
    app: Flask,
) -> set[str]:
    """
    Return the configured trusted hosts in normalized form.
    """

    trusted_hosts = app.config.get(
        "TRUSTED_HOSTS",
        [],
    )

    if not isinstance(
        trusted_hosts,
        (list, tuple, set),
    ):
        raise RuntimeError(
            "TRUSTED_HOSTS must be a list, tuple, or set."
        )

    normalized_hosts: set[str] = set()

    for trusted_host in trusted_hosts:
        if not isinstance(
            trusted_host,
            str,
        ):
            continue

        normalized_host = (
            trusted_host
            .strip()
            .lower()
        )

        if not normalized_host:
            continue

        # ----------------------------------------------------
        # Host entries must contain only a hostname.
        #
        # Do not silently accept:
        #   https://example.com
        #   example.com/path
        #   example.com:5000
        #
        # The actual request host is normalized separately.
        # ----------------------------------------------------

        if "://" in normalized_host:
            raise RuntimeError(
                "TRUSTED_HOSTS must contain hostnames only."
            )

        if "/" in normalized_host:
            raise RuntimeError(
                "TRUSTED_HOSTS entries cannot contain '/'."
            )

        normalized_hosts.add(
            normalized_host
        )

    return normalized_hosts


def _get_request_hostname() -> str:
    """
    Extract and normalize the hostname from the request.

    Flask/Werkzeug has already parsed the Host header for us.
    The port is removed before comparison.
    """

    host = request.host

    if not isinstance(
        host,
        str,
    ):
        return ""

    host = host.strip().lower()

    if not host:
        return ""

    # --------------------------------------------------------
    # IPv6 Host header
    #
    # Example:
    # [::1]:5000
    # --------------------------------------------------------

    if host.startswith("["):
        closing_bracket = host.find("]")

        if closing_bracket == -1:
            return ""

        return host[
            : closing_bracket + 1
        ]

    # --------------------------------------------------------
    # Normal hostname / IPv4
    # --------------------------------------------------------

    return host.split(
        ":",
        1,
    )[0]


# ============================================================
# MIDDLEWARE REGISTRATION
# ============================================================

def register_security_middleware(
    app: Flask,
) -> None:
    """
    Register request-level security middleware.
    """

    trusted_hosts = _get_normalized_trusted_hosts(
        app
    )

    @app.before_request
    def validate_request_host():
        """
        Reject requests whose Host header is not trusted.
        """

        # ----------------------------------------------------
        # If no trusted hosts are configured, fail closed.
        # ----------------------------------------------------

        if not trusted_hosts:
            return error_response(
                code="INVALID_HOST_CONFIGURATION",
                message=(
                    "The backend has no trusted hosts configured."
                ),
                status_code=500,
            )

        request_hostname = (
            _get_request_hostname()
        )

        if not request_hostname:
            return error_response(
                code="INVALID_HOST",
                message=(
                    "The requested host is invalid."
                ),
                status_code=400,
            )

        # ----------------------------------------------------
        # Exact host matching only.
        # ----------------------------------------------------

        if request_hostname not in trusted_hosts:
            app.logger.warning(
                "Rejected request from untrusted host: %s",
                request_hostname,
            )

            return error_response(
                code="INVALID_HOST",
                message=(
                    "The requested host is not allowed."
                ),
                status_code=400,
            )

        return None
