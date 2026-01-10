import http

import jwt
from fastapi import HTTPException, Request
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.id_token import verify_oauth2_token
from jwt import PyJWTError


def verify_authorized_request(request: Request, expected_audience: str) -> str:
    """Verify an authenticated request from a Cloud Run service.

    1. Extracts the token from the request headers.
    2. Decodes the token and validates its claims (`iss`, `aud`).

       NOTE: The signature is not validated when the token is provided using
       the `X-Serverless-Authorization` header.

    3. Returns the `email` claim.

    WARNING: Google automatically removes the signature of a JWT sent with the
    `X-Serverless-Authorization` header. Therefore, it is impossible to verify
    the token in the application code. For this reason, we must rely on Cloud
    Run's authenticating proxy and IAM for authentication if the token is
    provided using this header instead of the standard `Authorization` header.

    Furthermore, even if a service is publicly accessible, Google will still
    remove the signature of the JWT.

    Args:
        request: FastAPI Request object.
        expected_audience: Audience value the token must contain.

    Returns:
        Service account email from the validated token.

    Raises:
        HTTPException: If the token is missing, invalid, or malformed.

    Example:
        @app.get("/api/v1")
        def handle_request(request: Request):
            email = verify_authorized_request(
                request, expected_audience="https://my-service.run.app"
            )
            return email
    """
    auth_header = request.headers.get("Authorization")
    serverless_auth_header = request.headers.get("X-Serverless-Authorization")

    if not (auth_header or serverless_auth_header):
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Missing authorization header",
        )

    try:
        # If both headers are provided, only check the
        # `X-Serverless-Authorization` header.
        if serverless_auth_header:
            auth_type, token = serverless_auth_header.split(" ", 1)
        else:
            auth_type, token = auth_header.split(" ", 1)
    except ValueError:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Malformed authorization header",
        )

    if auth_type.lower() != "bearer":
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Unsupported authentication type: %s" % auth_type,
        )

    try:
        # WARNING: The following will always produce a 'Could not verify token
        # signature' error if the token is provided using the
        # `X-Serverless-Authorization` header:
        #
        #   claims = verify_oauth2_token(
        #       token, GoogleAuthRequest(), expected_audience
        #   )
        #
        # Therefore, the JWT must be decoded without verifying the signature.
        # If the service is publicly accessible, you can basically use whatever
        # JWT you want as long as it is added to the
        # `X-Serverless-Authorization` header and decodes properly.
        #
        # In order to verify the token via code, it must be provided using the
        # `Authorization` header. If both headers are provided, only the
        # `X-Serverless-Authorization` header is checked by the Google Cloud
        # Run platform.
        if serverless_auth_header:
            claims = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_aud": True,
                    "verify_iss": True,
                },
                audience=expected_audience,
                issuer=["https://accounts.google.com", "accounts.google.com"],
            )
        else:
            claims = verify_oauth2_token(
                token, GoogleAuthRequest(), expected_audience
            )
        email = claims.get("email")
        if not email:
            raise HTTPException(
                status_code=http.HTTPStatus.UNAUTHORIZED,
                detail="Token missing `email` claim",
            )
        return email
    except GoogleAuthError as exc:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Invalid token: %s" % exc,
        ) from exc
    except PyJWTError as exc:
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED,
            detail="Invalid token: %s" % exc,
        ) from exc
