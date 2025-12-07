from app.auth.token_manager import get_token
import os
import requests

BASE_URL = os.getenv("BASE_URL")
BRANCH = os.getenv("BRANCH")

def test_connection():
    token = get_token()
    
    url = f"{BASE_URL}/student?branch={BRANCH}&session=1"
    
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})

    return {"status": response.status_code, "response": response.text[:200]}
