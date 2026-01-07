import jwt
from fastapi import HTTPException, Request
from jwt import PyJWTError


def verify_authorized_request(request: Request, expected_audience: str) -> str:
    """Verify an authenticated request from a Cloud Run service.

    1. Extracts the token from the request headers.
    2. Decodes the token and validates its claims (`iss`, `aud`).
    3. Returns the `email` claim.

    WARNING: Google automatically removes the signature of a JWT sent with the
    `Authorization` or `X-Serverless-Authorization` header. Therefore, it is
    impossible to re-verify the token in the application code. For this reason,
    we must rely on Cloud Run's authenticating proxy and IAM for
    authentication.

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
    if not auth_header:
        auth_header = request.headers.get("X-Serverless-Authorization")

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        auth_type, token = auth_header.split(" ", 1)
    except ValueError:
        raise HTTPException(status_code=401, detail="Malformed Authorization header")

    if auth_type.lower() != "bearer":
        raise HTTPException(
            status_code=401, detail=f"Unsupported authentication type: {auth_type}"
        )

    try:
        # WARNING: The following will always produce a 'Could not verify token
        # signature' error:
        #
        #   claims = id_token.verify_oauth2_token(
        #       token, GoogleAuthRequest(), expected_audience
        #   )
        #
        # Therefore, the JWT must be decoded without verifying the signature.
        # If the service is publicly accessible, you can basically use whatever
        # JWT you want as long as it is added to the `Authorization` or
        # `X-Serverless-Authorization` header and decodes properly.
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
        email = claims.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token missing `email` claim")
        return email
    except PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc
