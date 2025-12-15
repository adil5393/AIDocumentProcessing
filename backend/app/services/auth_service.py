import os
import json
import time
import requests

TOKEN_FILE = "token_cache.json"
TOKEN_EXPIRY_FILE = "token_expiry.json"

BASE_URL = os.getenv("BASE_URL")
LOGIN_URL = f"{BASE_URL}/auth/login"

TOKEN_VALIDATION_URL = f"{BASE_URL}/userschool/"

AMTECH_USERNAME = os.getenv("AMTECH_USERNAME")
AMTECH_PASSWORD = os.getenv("AMTECH_PASSWORD")


def save_token(token, expires_in_seconds, user_id):
    expiry = time.time() + expires_in_seconds

    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token, "user_id": user_id}, f)
    with open(TOKEN_EXPIRY_FILE, "w") as f:
        json.dump({"expiry": expiry}, f)

def load_token():
    if not os.path.exists(TOKEN_FILE) or not os.path.exists(TOKEN_EXPIRY_FILE):
        return None, None, None
    with open(TOKEN_FILE, "r") as f:
        data = json.load(f)
        token = data["token"]
        user_id = data["user_id"]

    with open(TOKEN_EXPIRY_FILE, "r") as f:
        expiry = json.load(f)["expiry"]

    return token, expiry, user_id

def is_token_valid(token, user_id):
    url = f"{TOKEN_VALIDATION_URL}{user_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://amtech-school.com",
        "Referer": "https://amtech-school.com/",
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    print("VALIDATION STATUS:", response.status_code, response.text)

    return response.status_code == 200

def authenticate():
    token, expiry, user_id = load_token()

    # Token exists and still valid
    if token and expiry > time.time() and is_token_valid(token,user_id):
        return token

    # Otherwise request new token
    login_payload = {
        "username": AMTECH_USERNAME,
        "password": AMTECH_PASSWORD
    }

    response = requests.post(LOGIN_URL, json=login_payload)

    if response.status_code in (200, 201):
        data = response.json()
        
        # Real token structure
        token = data["token"]
        user_id = data["user"]["user_id"]

        # If the API doesn't tell expiry, assume 30 days, or pick a safe default
        expires = 60 * 60 * 24 * 30  # 30 days
        
        save_token(token, expires,user_id)
        return token

    raise Exception(f"Auth failed: {response.text}")
