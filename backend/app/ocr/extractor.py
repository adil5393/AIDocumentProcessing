from openai import OpenAI
import os
import json
import re

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_gpt(prompt: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You extract structured data from documents. Output ONLY valid JSON. No markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    # Remove ```json ... ``` if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "error": "invalid_json",
            "raw_response": content
        }


def extract_admission_form(text: str) -> dict:
    prompt = f"""
Extract fields from a SCHOOL ADMISSION FORM.

Fields:
- sr
- class
- student_name
- gender
- date_of_birth (YYYY-MM-DD)
- father_name
- mother_name
- father_occupation
- mother_occupation
- address
- phone1
- phone2
- aadhaar_number
- last_school_attended

Rules:
- Return ONLY valid JSON
- If a field is missing, use null
- Phone numbers digits only or null

OCR Text:
\"\"\"
{text}
\"\"\"
"""
    return call_gpt(prompt)

def extract_aadhaar(text: str) -> dict:
    prompt = f"""
Extract fields from an AADHAAR CARD.

Fields:
- name
- date_of_birth (YYYY-MM-DD)
- aadhaar_number

Rules:
- Aadhaar number must be exactly 12 digits or null
- Return ONLY valid JSON
- Do NOT infer relationships
- Do NOT guess role (student/parent)
- Return name in English only


OCR Text:
\"\"\"
{text}
\"\"\"
"""
    return call_gpt(prompt)

def extract_transfer_certificate(text: str) -> dict:
    prompt = f"""
Extract fields from a TRANSFER CERTIFICATE.

Fields:
- student_name
- father_name
- mother_name
- date_of_birth (YYYY-MM-DD)
- last_class_studied
- last_school_name

Rules:
- Return ONLY valid JSON
- If missing, use null
- Return Name only in English
- Use Indian Naming Convention

OCR Text:
\"\"\"
{text}
\"\"\"
"""
    return call_gpt(prompt)

def extract_marksheet(text: str) -> dict:
    prompt = f"""
Extract fields from a HIGH SCHOOL MARKSHEET.

Fields:
- student_name
- father_name
- mother_name
- date_of_birth (YYYY-MM-DD)
- result_status (PASS or FAIL)

Rules:
- Return ONLY valid JSON
- Do NOT guess values

OCR Text:
\"\"\"
{text}
\"\"\"
"""
    return call_gpt(prompt)

def extract_birth_certificate(text: str) -> dict:
    prompt = f"""
Extract fields from a BIRTH CERTIFICATE.

Fields:
- student_name
- father_name
- mother_name
- date_of_birth (YYYY-MM-DD)
- place_of_birth

Rules:
- Return ONLY valid JSON
- Do NOT guess values

OCR Text:
\"\"\"
{text}
\"\"\"
"""
    return call_gpt(prompt)




def extract_fields(doc_type: str, raw_text: str) -> dict:
    if doc_type == "admission_form":
        return extract_admission_form(raw_text)

    if doc_type == "aadhaar":
        return extract_aadhaar(raw_text)

    if doc_type == "transfer_certificate":
        return extract_transfer_certificate(raw_text)

    if doc_type == "marksheet":
        return extract_marksheet(raw_text)

    if doc_type == "birth_certificate":
        return extract_birth_certificate(raw_text)

    return {"error": "unsupported_document_type"}
