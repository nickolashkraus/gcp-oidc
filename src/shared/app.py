"""
Shared FastAPI application.
"""

import logging

from fastapi import FastAPI
from google.cloud import logging as cloud_logging


def create_app(app_name: str) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title=app_name)

    @app.on_event("startup")
    async def _startup() -> None:
        configure_cloud_logging()

    return app


def configure_cloud_logging() -> None:
    """
    Initialize Google Cloud Logging and attach handler.

    Allows Python's standard logging to emit to Google Cloud logging. Setup
    failure allows app to run with standard logging.
    """
    try:
        client = cloud_logging.Client()
        client.setup_logging(log_level=logging.INFO)
        logging.getLogger().setLevel(logging.INFO)
    except Exception as exc:
        logging.warning(
            "Google Cloud Logging setup failed, using standard logging: %s", exc
        )
