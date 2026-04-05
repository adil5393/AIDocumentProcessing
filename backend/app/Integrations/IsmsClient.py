import requests
from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

ISMS_BASE_URL = os.getenv("ISMS_BASE_URL", "").rstrip("/")


def isms_get(path: str, token: str, params: dict | None = None):
    """
    Generic GET helper for ISMS ERP API.
    Uses Token authentication (Django REST Framework default).
    """
    url = f"{ISMS_BASE_URL}{path}"

    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.RequestException as e:
        raise HTTPException(502, f"ISMS ERP connection error: {e}")

    if resp.status_code in (401, 403):
        raise HTTPException(401, "ISMS ERP authentication failed")

    if not resp.ok:
        raise HTTPException(
            resp.status_code,
            f"ISMS ERP error {resp.status_code}: {resp.text}"
        )

    try:
        return resp.json()
    except ValueError:
        raise HTTPException(500, "Invalid JSON from ISMS ERP")


def isms_post(path: str, token: str, payload: dict):
    """
    JSON POST to ISMS ERP (e.g. POST /api/students/).
    Uses Token authentication (Django REST Framework default).
    """
    url = f"{ISMS_BASE_URL}{path}"

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    import logging
    _log = logging.getLogger(__name__)

    resp = requests.post(url, headers=headers, json=payload, timeout=20)

    _log.debug("ISMS ERP POST %s -> %s", path, resp.status_code)

    try:
        resp_json = resp.json()
    except ValueError:
        resp_json = None

    return {
        "status_code": resp.status_code,
        "json": resp_json,
    }

