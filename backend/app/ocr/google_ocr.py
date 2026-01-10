from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account
import mimetypes
from dotenv import load_dotenv
import os

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
PROCESSOR_ID = os.getenv("PROCESSOR_ID")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")  # fallback

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE
)


processor_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
# print(PROJECT_ID,LOCATION,PROCESSOR_ID,UPLOADS_DIR, processor_name)
client = documentai.DocumentProcessorServiceClient(
    credentials=credentials
)


def process_file(file_path: str) -> str:
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

    # 🔹 OCR PROCESSOR RETURNS TEXT ONLY
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
