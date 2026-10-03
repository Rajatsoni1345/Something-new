"""
Birthday Quest - Request ID Middleware

Assigns a unique request ID to every incoming request and
returns it to the client through the X-Request-ID header.
"""

from __future__ import annotations

from flask import Flask, g, request

from utils.ids import generate_request_id
from utils.logging import log_info


# ------------------------------------------------------------
# HEADER NAME
# ------------------------------------------------------------

REQUEST_ID_HEADER = "X-Request-ID"


# ------------------------------------------------------------
# REGISTRATION
# ------------------------------------------------------------

def register_request_id_middleware(app: Flask) -> None:
    """
    Register request ID handling with the Flask application.
    """

    @app.before_request
    def attach_request_id() -> None:
        """
        Use a client-supplied request ID only when it is a valid,
        bounded identifier. Otherwise generate a fresh one.
        """

        incoming_request_id = request.headers.get(
            REQUEST_ID_HEADER
        )

        if (
            incoming_request_id
            and 1 <= len(incoming_request_id) <= 128
            and incoming_request_id.isprintable()
        ):
            request_id = incoming_request_id
        else:
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
    def attach_request_id_header(response):
        """
        Return the request ID to the client.
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
