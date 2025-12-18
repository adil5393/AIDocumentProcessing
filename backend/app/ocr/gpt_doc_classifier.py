from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You classify document types."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    return result if result in ALLOWED_TYPES else "unknown"
