from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account
from google.auth import default
import mimetypes
from dotenv import load_dotenv
import os

load_dotenv()

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

PROJECT_ID   = os.getenv("DEV_PROJECT_ID"  if DEV_MODE else "PROJECT_ID")
LOCATION     = os.getenv("DEV_LOCATION"    if DEV_MODE else "LOCATION")
PROCESSOR_ID = os.getenv("DEV_PROCESSOR_ID" if DEV_MODE else "PROCESSOR_ID")
UPLOADS_DIR  = os.getenv("UPLOADS_DIR", "uploads")

_client = None
_processor_name = None


def _get_client():
    global _client, _processor_name
    if _client is not None:
        return _client, _processor_name

    if DEV_MODE:
        os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
        credentials, _ = default()
    else:
        sa_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not sa_file:
            raise RuntimeError(
                "GOOGLE_APPLICATION_CREDENTIALS env var is not set. "
                "Point it to your service-account JSON file."
            )
        credentials = service_account.Credentials.from_service_account_file(sa_file)

    _processor_name = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    )
    _client = documentai.DocumentProcessorServiceClient(credentials=credentials)
    return _client, _processor_name


def process_file(file_path: str) -> str:
    if DEV_MODE:
        return f"DEV OCR placeholder for {os.path.basename(file_path)}"

    client, processor_name = _get_client()

    mime_type = mimetypes.guess_type(file_path)[0]

    if not mime_type:
        raise ValueError(f"Cannot determine mime type for {file_path}")

    with open(file_path, "rb") as f:
        content = f.read()

    raw_document = documentai.RawDocument(
        content=content,
        mime_type=mime_type
    )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=raw_document
    )

    result = client.process_document(request=request)
    document = result.document

    return document.text


def process_all_uploads():
    results = []

    for filename in os.listdir(UPLOADS_DIR):
        file_path = os.path.join(UPLOADS_DIR, filename)

        if not os.path.isfile(file_path):
            continue

        print(f"\n🔍 Processing: {filename}")

        try:
            ocr_text = process_file(file_path)

            results.append({
                "file": filename,
                "text": ocr_text
            })

            print("✅ OCR done")

        except Exception as e:
            print(f"❌ Failed OCR for {filename}: {e}")
            results.append({
                "file": filename,
                "error": str(e)
            })

    return results


if __name__ == "__main__":
    outputs = process_all_uploads()
    for out in outputs:
        print("\n==== OCR OUTPUT ====")
        print(out)
