import requests
from fastapi import HTTPException
from dotenv import load_dotenv
import os
load_dotenv()


AMTECH_BASE_URL = os.getenv('AMTECH_BASE_URL')

def amtech_get(path: str, token: str, params: dict | None = None):
    """
    Generic GET helper for Amtech API
    """
    url = f"{AMTECH_BASE_URL}{path}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    try:
        resp = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
    except requests.RequestException as e:
        raise HTTPException(502, f"Amtech connection error: {e}")

    # 🔐 Auth failure
    if resp.status_code in (401, 403):
        raise HTTPException(401, "Amtech authentication failed")

    # ❌ Any other failure
    if not resp.ok:
        raise HTTPException(
            resp.status_code,
            f"Amtech error {resp.status_code}: {resp.text}"
        )

    try:
        return resp.json()
    except ValueError:
        raise HTTPException(500, "Invalid JSON from Amtech")

def amtech_post(path: str, token: str, data: list):
    import requests
    from fastapi import HTTPException

    url = f"{AMTECH_BASE_URL}{path}"

    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # payload = data[0]
    payload = data[0]
    
    branch_id = data[1]
    print(payload)
    files = {k: (None, str(v)) for k, v in payload.items()}

    resp = requests.post(
        url,
        headers=headers,
        params={"branch": branch_id},
        files=files,
        timeout=20
    )

    # 🔎 DEBUG OUTPUT (CRITICAL)
    print("AMTECH STATUS CODE:", resp.status_code)
    print("AMTECH HEADERS:", resp.headers)
    print("AMTECH RAW TEXT:", resp.text)

    # Try JSON, but don't force it
    try:
        resp_json = resp.json()
    except ValueError:
        resp_json = None

    # TEMP: return everything so you can see it in browser
    return {
        "status_code": resp.status_code,
        "headers": dict(resp.headers),
        "text": resp.text,
        "json": resp_json
    }
