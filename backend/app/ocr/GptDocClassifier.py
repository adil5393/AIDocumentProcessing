from openai import OpenAI
import os

_client = None

def _get_openai():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY env var is not set.")
        _client = OpenAI(api_key=api_key)
    return _client

ALLOWED_TYPES = [
    "admission_form",
    "aadhaar",
    "transfer_certificate",
    "birth_certificate",
    "marksheet",
    "unknown"
]

def gpt_detect_document_type(raw_text: str) -> str:
    prompt = f"""
You are a document classifier.

Based ONLY on the OCR text below, classify the document into ONE of the following types:

- admission_form
- aadhaar
- transfer_certificate
- birth_certificate
- marksheet
- unknown

Rules:
- Return ONLY one of the above values
- Do NOT explain
- If ambiguous, return "unknown"

OCR text:
\"\"\"
{raw_text[:]}
\"\"\"
"""

    response = _get_openai().chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You classify document types."},
        ])

    result = response.choices[0].message.content.strip()

    return result if result in ALLOWED_TYPES else "unknown"
