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
You are extracting structured data from a SCHOOL ADMISSION FORM.

You MUST follow the schema and rules exactly.

====================
OUTPUT SCHEMA (JSON)
====================

{{
  "sr": string | null,
  "class": string | null,
  "student_name": string | null,
  "gender": "Male" | "Female" | null,
  "date_of_birth": "YYYY-MM-DD" | null,
  "father_name": string | null,
  "mother_name": string | null,
  "mother_occupation": string | null,
  "father_occupation": string | null,
  "father_aadhaar": string | null,
  "mother_aadhaar": string | null,
  "student_aadhaar_number": string | null,
<<<<<<< HEAD
  "spen_number": string | null,
=======
  "spen": string | null,
>>>>>>> 1c6054e46ac1c4d19b999202615ecf67a3056284
  "address": string | null,
  "phone1": string | null,
  "phone2": string | null,
  "last_school_attended": string | null
}}

====================
HARD RULES (MANDATORY)
====================

1. Return ONLY valid JSON. No text outside JSON.
3. Aadhaar numbers:
   - Must be EXACTLY 12 digits
   - Must appear near keywords like "Aadhaar", "UID", "UIDAI"
   - MUST NOT be phone numbers
4. Phone numbers:
   - Must be EXACTLY 10 digits
   - Must appear near keywords like "Mobile", "Phone", "Contact","E-Mail".
   - MUST NOT be copied into Aadhaar fields
5. If a 10-digit number is found, DO NOT place it in any Aadhaar field.
6. If a 12-digit number is found near "Mobile" or "Phone", IGNORE it.
<<<<<<< HEAD
8. Use "spen_number" for SPEN / PEN interchangeably.
=======
8. Use "spen" for SPEN NUMBER / PEN NUMBER interchangeably.
>>>>>>> 1c6054e46ac1c4d19b999202615ecf67a3056284
9. Use Arabic numerals only (Always convert Roman numerals).
10. Give values of class only as integers wrapped as text.
NOTE:
Aadhaar numbers may be written with spaces or separators near "Aadhaar No. (Not mandatory) (Attach proof)" (e.g. 1234 5678 9012, 1.2.34.567.8 9 0.12).
Normalize them to a 12-digit string WITHOUT spaces.

====================
OCR TEXT
====================
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
- relation_type        (S/O, D/O, W/O or null)
- related_name         (name mentioned after relation, or null)

Rules:
- Aadhaar number must be exactly 12 digits or null
- Extract relation_type ONLY if explicitly present in text (S/O, D/O, W/O, C/O)
- Extract related_name ONLY if it appears next to relation_type
- Do NOT infer or guess relationships
- Do NOT decide whether Aadhaar belongs to student or parent
- Do NOT translate names
- Return names in English only
- Return null for any field not found
- Return ONLY valid JSON (no markdown, no explanation)

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
- All names MUST be returned in English (Latin alphabet)
- If a name appears in Hindi (Devanagari), TRANSLITERATE it to English
  using standard Indian phonetic transliteration (not translation)
  Example: "राम कुमार" → "Ram Kumar"
- If a name is already in English, preserve it verbatim
- If a name contains a title such as "Mr", "Mrs", "Ms", "Miss", "Smt", "Shri",
  KEEP the title exactly as it appears in the document
- Do NOT remove titles or honorifics
- Do NOT invent titles if not present
- Preserve original spacing and capitalization AFTER transliteration
- If a field is missing, use null
- Use Indian naming convention
- Convert Roman numerals in class names to integers (as strings)

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
You are extracting structured data from a BIRTH CERTIFICATE.

The OCR text may contain:
- encoding artifacts (garbled characters like αñªαñ┐)
- mixed languages (Hindi + English)
- duplicated names (one corrupted, one readable)

Your job is to return CLEAN, HUMAN-READABLE ENGLISH values only.

Fields to extract:
- student_name
- father_name
- mother_name
- date_of_birth (YYYY-MM-DD)
- place_of_birth

STRICT RULES:
- Return ONLY valid JSON
- Use ONLY standard ASCII characters (A–Z, a–z, spaces)
- If multiple versions of a name exist, choose the CLEAN ENGLISH one
- If text is in Hindi, transliterate to English
- If a value is unreadable or missing, return null
- Do NOT guess or infer missing values
- Remove all encoding junk and symbols
- Normalize date_of_birth to YYYY-MM-DD

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
