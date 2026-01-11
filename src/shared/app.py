"""
Shared FastAPI application.
"""

import logging

from fastapi import FastAPI
from google.cloud import logging as cloud_logging


def create_app(app_name: str, debug: bool = False) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title=app_name, debug=debug)

    @app.on_event("startup")
    async def _startup() -> None:
        configure_cloud_logging(debug=debug)

    return app


def configure_cloud_logging(debug: bool = False) -> None:
    """
    Initialize Google Cloud Logging and attach handler.

    Allows Python's standard logging to emit to Google Cloud logging. Setup
    failure allows app to run with standard logging.
    """
    log_level = logging.DEBUG if debug else logging.INFO
    try:
        client = cloud_logging.Client()
        client.setup_logging(log_level=log_level)
        logging.getLogger().setLevel(log_level)
    except Exception as exc:
        logging.warning(
            "Google Cloud Logging setup failed, using standard logging: %s", exc
        )
