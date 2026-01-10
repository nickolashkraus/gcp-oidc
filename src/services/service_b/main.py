"""Service B (Receiving Service).

Service B can receive authenticated requests from Service A.
"""

import http
import logging

import fastapi
import jwt
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.id_token import verify_oauth2_token
from jwt import PyJWTError

from services.service_b import settings
from shared.app import create_app

app_settings = settings.get_settings()
app = create_app(app_name=app_settings.app_name)


@app.get("/")
async def root(request: fastapi.Request):
    """Receive an authenticated request from Service A.

    Handles both `Authorization` and `X-Serverless-Authorization` headers.
      - If `Authorization` is used, verifies the token using the Google Auth
        Python Library.
      - If `X-Serverless-Authorization` is used, simply decode the token, since
        Google automatically removes the token's signature.

    If both headers are provided, only the `X-Serverless-Authorization` header
    is used.
    """
    if app_settings.debug:
        logging.debug(f"Headers: {request.headers}")

    auth_header = request.headers.get("Authorization")
    serverless_auth_header = request.headers.get("X-Serverless-Authorization")

    if not (auth_header or serverless_auth_header):
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Missing authorization header",
        )

    # Use `X-Serverless-Authorization` if provided.
    is_x_serverless_authorization = False
    if serverless_auth_header:
        auth_header = serverless_auth_header
        is_x_serverless_authorization = True

    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    if app_settings.debug:
        logging.debug(f"Token: {token}")

    # If `Authorization` is used, verify the token.
    if not is_x_serverless_authorization:
        try:
            claims = verify_oauth2_token(
                id_token=token,
                request=GoogleAuthRequest(),
                audience=app_settings.service_b_url,
            )
            logging.info(f"Token verification succeeded. Claims: {claims}")
        except GoogleAuthError as exc:
            logging.error(f"Token verification failed: {exc}")
            raise fastapi.HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Invalid token: %s" % exc,
            ) from exc
    # If `X-Serverless-Authorization` is used, simply decode the token.
    # The signature cannot be verified, since it is removed by Google (replaced
    # with `SIGNATURE_REMOVED_BY_GOOGLE`). We are still able to validate the
    # audience and issuer, however.
    else:
        try:
            claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_aud": True,
                    "verify_iss": True,
                },
                audience=app_settings.service_b_url,
                issuer=["https://accounts.google.com", "accounts.google.com"],
            )
            logging.info(f"Decoded token: {claims}")
        except PyJWTError as exc:
            logging.error(f"Failed to decode token: {exc}")
            raise fastapi.HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Malformed token: %s" % exc,
            ) from exc

    email = claims.get("email")
    if not email:
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Missing or empty `email` claim on token",
        )

    return {"message": f"Credentials: {email}"}
