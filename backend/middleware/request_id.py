"""
Birthday Quest - Request ID Middleware

Assigns a trusted server-generated request ID to every incoming
request and returns it through the X-Request-ID response header.

IMPORTANT:
- Request IDs are generated server-side.
- Client-provided request IDs are NOT trusted.
- Request IDs are useful for logs, diagnostics, and audit events.
"""

from __future__ import annotations

from flask import Flask, g, request

from utils.ids import generate_request_id
from utils.logging import log_info


REQUEST_ID_HEADER = "X-Request-ID"


def register_request_id_middleware(
    app: Flask,
) -> None:
    """
    Register request ID middleware.
    """

    @app.before_request
    def attach_request_id() -> None:
        """
        Generate a fresh trusted request ID for every request.

        A client may send an X-Request-ID header, but it is never
        reused because the backend must control its own diagnostic
        identifiers.
        """

        request_id = generate_request_id()

        g.request_id = request_id

        log_info(
            app.logger,
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.path,
        )

    @app.after_request
    def attach_request_id_header(
        response,
    ):
        """
        Return the trusted request ID to the client.
        """

        request_id = getattr(
            g,
            "request_id",
            None,
        )

        if request_id:
            response.headers[
                REQUEST_ID_HEADER
            ] = request_id

        return response
