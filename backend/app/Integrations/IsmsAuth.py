import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_FILE = "token_cache.json"
TOKEN_EXPIRY_FILE = "token_expiry.json"

# ISMS ERP 
ISMS_BASE_URL = os.getenv("ISMS_BASE_URL", "").rstrip("/")
ISMS_USERNAME = os.getenv("ISMS_USERNAME")
ISMS_PASSWORD = os.getenv("ISMS_PASSWORD")

LOGIN_URL = f"{ISMS_BASE_URL}/api/auth/login/"
VALIDATE_URL = f"{ISMS_BASE_URL}/api/auth/user/"


def save_token(token: str, expires_in_seconds: float, user_id):
    expiry = time.time() + expires_in_seconds

    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token, "user_id": user_id}, f)

    with open(TOKEN_EXPIRY_FILE, "w") as f:
        json.dump({"expiry": expiry}, f)


def load_token():
    """Returns (token, expiry, user_id). All None if not cached."""
    if not os.path.exists(TOKEN_FILE) or not os.path.exists(TOKEN_EXPIRY_FILE):
        return None, None, None

    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
        token = data.get("token")
        user_id = data.get("user_id")

    with open(TOKEN_EXPIRY_FILE, "r") as f:
        expiry = json.load(f)["expiry"]

    return token, expiry, user_id


def is_token_valid(token: str):
    """
    Validate token against ISMS ERP GET /api/auth/user/.
    Returns (is_valid: bool, user_data: dict | None).
    """
    if not token:
        return False, None

    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
    }

    try:
        response = requests.get(VALIDATE_URL, headers=headers, timeout=10)
    except requests.RequestException as e:
        print(f"ISMS ERP validation error: {e}")
        return False, None

    print("ISMS ERP VALIDATION STATUS:", response.status_code)

    if response.status_code != 200:
        return False, None

    try:
        return True, response.json()
    except ValueError:
        return False, None


def authenticate():
    """
    Login to ISMS ERP and cache the token.
    Skips login if cached token is still valid.
    Returns the token string.
    """
    token, expiry, user_id = load_token()

    valid, _ = is_token_valid(token)
    if token and expiry and expiry > time.time() and valid:
        return token

    login_payload = {
        "username": ISMS_USERNAME,
        "password": ISMS_PASSWORD,
    }

    try:
        response = requests.post(LOGIN_URL, json=login_payload, timeout=15)
    except requests.RequestException as e:
        raise Exception(f"ISMS ERP login request failed: {e}")

    if response.status_code not in (200, 201):
        raise Exception(f"ISMS ERP auth failed [{response.status_code}]: {response.text}")

    data = response.json()
    token = data["token"]
    user_id = data["user"]["id"]   # ISMS ERP uses "id", not "user_id"

    # DRF tokens don't expire; re-validate every 24 h
    save_token(token, 60 * 60 * 24, user_id)

    print(f"ISMS ERP authenticated: user_id={user_id}")
    return token
