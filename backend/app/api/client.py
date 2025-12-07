import requests
from auth.token_manager import get_token, request_new_token

def api_request(method, url, **kwargs):
    """Auto handles refresh if token expires"""
    token = get_token()

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"

    response = requests.request(method, url, headers=headers, **kwargs)

    # If token expired
    if response.status_code == 401:
        new_token = request_new_token()
        headers["Authorization"] = f"Bearer {new_token}"
        response = requests.request(method, url, headers=headers, **kwargs)

    return response
