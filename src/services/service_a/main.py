"""Service A (Calling Service).

Service A can make authenticated requests to Service B.
"""

import http
import logging

import fastapi
import httpx
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.id_token import fetch_id_token

from services.service_a import settings
from shared.app import create_app

app_settings = settings.get_settings()
app = create_app(app_name=app_settings.app_name)


@app.get("/")
async def root(
    request: fastapi.Request,
    use_x_serverless_authorization: bool = False,
):
    """Make an authenticated request to Service B.

    Set the `use_x_serverless_authorization` to true to use the
    `X-Serverless-Authorization` header. Defaults to using the `Authorization`
    header.
    """
    try:
        token = fetch_id_token(
            request=GoogleAuthRequest(),
            audience=app_settings.service_b_url,
        )
    except GoogleAuthError as exc:
        logging.error("Failed to fetch ID token: %s", exc)
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Failed to fetch ID token",
        ) from exc

    url = app_settings.service_b_url

    if use_x_serverless_authorization:
        headers = {
            "X-Serverless-Authorization": f"Bearer {token}",
        }
    else:
        headers = {
            "Authorization": f"Bearer {token}",
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=http.HTTPMethod.GET, url=url, headers=headers
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise fastapi.HTTPException(
            status_code=exc.response.status_code, detail=exc.response.text
        ) from exc
    except httpx.RequestError as exc:
        logging.error("Error calling Service B: %s", exc)
        raise fastapi.HTTPException(
            status_code=http.HTTPStatus.BAD_GATEWAY,
            detail="Failed to reach Service B",
        ) from exc

    return fastapi.Response(
        content=response.text,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json"),
    )
