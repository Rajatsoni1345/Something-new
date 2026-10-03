"""
Birthday Quest - Security Middleware

Request-level security checks.

Responsibilities:
- Validate the incoming Host header.
- Reject requests for untrusted hosts.
- Keep host validation centralized.
- Fail closed when trusted-host configuration is invalid.

Admin authentication/authorization does NOT belong here.
It is handled separately by the admin route/service layer.
"""

from __future__ import annotations

from flask import Flask, request

from utils.responses import error_response


# ============================================================
# HOST CONFIGURATION
# ============================================================

def _get_normalized_trusted_hosts(
    app: Flask,
) -> set[str]:
    """
    Return configured trusted hosts in normalized form.

    Trusted hosts must contain hostnames only.

    Valid examples:
        example.com
        api.example.com
        localhost
        127.0.0.1
        [::1]

    Invalid examples:
        https://example.com
        example.com/path
        example.com:5000
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
            raise RuntimeError(
                "Every TRUSTED_HOSTS entry must be a string."
            )

        normalized_host = (
            trusted_host
            .strip()
            .lower()
        )

        if not normalized_host:
            continue

        # ----------------------------------------------------
        # Never silently normalize a URL into a hostname.
        # ----------------------------------------------------

        if "://" in normalized_host:
            raise RuntimeError(
                "TRUSTED_HOSTS must contain hostnames only."
            )

        if "/" in normalized_host:
            raise RuntimeError(
                "TRUSTED_HOSTS entries cannot contain '/'."
            )

        # ----------------------------------------------------
        # A trusted host must not contain a port.
        # ----------------------------------------------------

        if normalized_host.startswith("["):
            closing_bracket = normalized_host.find("]")

            if closing_bracket == -1:
                raise RuntimeError(
                    "Invalid IPv6 entry in TRUSTED_HOSTS."
                )

            if normalized_host[
                closing_bracket + 1:
            ]:
                raise RuntimeError(
                    "TRUSTED_HOSTS entries cannot contain ports."
                )

        elif ":" in normalized_host:
            raise RuntimeError(
                "TRUSTED_HOSTS entries cannot contain ports."
            )

        normalized_hosts.add(
            normalized_host
        )

    return normalized_hosts


# ============================================================
# REQUEST HOST NORMALIZATION
# ============================================================

def _get_request_hostname() -> str:
    """
    Extract the hostname from the current request.

    Flask/Werkzeug parses the Host header before this function
    runs. The port is removed before exact comparison.
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
    # IPv6
    #
    # Examples:
    #   [::1]
    #   [::1]:5000
    # --------------------------------------------------------

    if host.startswith("["):
        closing_bracket = host.find("]")

        if closing_bracket == -1:
            return ""

        hostname = host[
            : closing_bracket + 1
        ]

        return hostname

    # --------------------------------------------------------
    # Normal hostname / IPv4.
    #
    # Example:
    #   example.com:5000
    #       -> example.com
    # --------------------------------------------------------

    if ":" in host:
        return host.split(
            ":",
            1,
        )[0]

    return host


# ============================================================
# MIDDLEWARE REGISTRATION
# ============================================================

def register_security_middleware(
    app: Flask,
) -> None:
    """
    Register request-level host validation middleware.

    The configuration is validated during application startup,
    while every incoming request is checked against the
    resulting exact host allowlist.
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
        # Fail closed if no trusted host is configured.
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
        # Exact matching only.
        #
        # No wildcard/subdomain guessing is performed.
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
