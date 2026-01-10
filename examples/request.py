import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.id_token import fetch_id_token


def make_authorized_request(endpoint: str, audience: str) -> requests.Response:
    """Make an authenticated request to a Cloud Run service.

    The request is authenticated using the ID token obtained from the
    google-auth client library using the specified audience value.

    NOTE: Cloud Run's authenticating proxy uses the `aud` claim to validate the
    token. Therefore, you must set the audience to the URL of the receiving
    service. The endpoint is the API endpoint (base URL + path) that will
    receive/handle the request.

    See:
      - https://github.com/googleapis/google-auth-library-python

    Args:
        endpoint: URL of the request (e.g., https://service.run.app/api/v1/).
        audience: Cloud Run service URL used for token validation (typically
            the same as endpoint's base URL unless using a custom audience).

    Returns:
        HTTP response for the request.

    Raises:
        requests.HTTPError: If the request returns an error status code.
        google.auth.exceptions.GoogleAuthError: If token retrieval fails.

    Example:
        response = make_authorized_request(
            endpoint='https://service-b.a.run.app/api/v1/',
            audience='https://service-b.a.run.app'
        )
    """
    token = fetch_id_token(GoogleAuthRequest(), audience)

    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(endpoint, headers=headers)
    resp.raise_for_status()

    return resp
