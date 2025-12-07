from api.client import api_request
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
BRANCH = os.getenv("BRANCH")

url = f"{BASE_URL}/student?branch={BRANCH}&session=1"
resp = api_request("GET", url)

print("Status:", resp.status_code)
print("Response:", resp.text[:500])
