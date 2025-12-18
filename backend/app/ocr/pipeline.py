from .google_ocr import process_all_uploads
from .extractor import extract_fields
from .doc_classifier import detect_document_type
from .gpt_doc_classifier import gpt_detect_document_type

def run():
    ocr_results = process_all_uploads()

    for item in ocr_results:
        print(f"\n📄 File: {item['file']}")

        if "error" in item:
            print("❌ OCR failed:", item["error"])
            continue

        text = item["text"]

        # 🔹 THIS is where doc_type comes from
        doc_type = detect_document_type(text)
        
        if doc_type == "unknown":
            doc_type = gpt_detect_document_type(text)
        print("Document Type: ",doc_type)
        structured = extract_fields(doc_type, text)

        print("\n==== STRUCTURED RESULT ====")
        print(structured)


if __name__ == "__main__":
    run()
