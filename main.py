import logging

import fastapi
import jwt
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.id_token import fetch_id_token, verify_oauth2_token

app = fastapi.FastAPI()

AUDIENCE = "https://hello-jk5drksivq-uc.a.run.app"


@app.get("/")
async def root():
    token = fetch_id_token(request=GoogleAuthRequest(), audience=AUDIENCE)
    credentials = await verify_oidc_token(token=token)
    logging.info(f"Credentials: {credentials}")
    return {"message": f"Credentials: {credentials}"}


async def verify_oidc_token(
    token: str,
) -> fastapi.security.http.HTTPAuthorizationCredentials:
    """Verify a Google-signed OpenID Connect ID token with enhanced debugging."""
    # 1. Log actual token.
    logging.info(f"Token: {token}")

    # 2. Attempt to decode JWT without verification.
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        logging.info(f"Decoded token: {decoded}")
    except Exception as exc:
        logging.error(f"Failed to decode token: {exc}")
        raise fastapi.HTTPException(status_code=401, detail="Malformed token") from exc

    # 3. Attempt to verify token.
    try:
        claims = verify_oauth2_token(id_token=token, request=GoogleAuthRequest())
        logging.info(f"Token verification succeeded. Claims: {claims}")
    except GoogleAuthError as exc:
        logging.error(f"Token verification failed: {exc}")
        raise fastapi.HTTPException(
            status_code=401,
            detail=f"Invalid token: {exc}",
        ) from exc

    # 4. Attempt to verify token with audience.
    # try:
    #     claims = id_token.verify_oauth2_token(token, GoogleAuthRequest())
    #     logging.info(f"Token verification succeeded. Claims: {claims}")
    # except google_auth_exceptions.GoogleAuthError as exc:
    #     logging.error(f"Token verification failed: {exc}")
    #     raise HTTPException(
    #         status_code=401,
    #         detail=f"Invalid token: {exc}",
    #     ) from exc

    # 5. Attempt to extract email from claims.
    email = claims.get("email")
    if not email:
        raise fastapi.HTTPException(
            status_code=401,
            detail="Missing or empty `email` claim on token",
        )

    return fastapi.security.http.HTTPAuthorizationCredentials(
        scheme="", credentials=email
    )
