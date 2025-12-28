from pdf2image import convert_from_path
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()


PREVIEW_DIR = Path(os.getenv("PREVIEW_DIR", "uploads\\previews"))
POPPLER_PATH = Path(r"C:\poppler-25.12.0\Library\bin")

def generate_preview_image(pdf_path: str) -> str:
    pdf_path = Path(pdf_path)

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    output_name = pdf_path.stem  # 🔑 safe filename
    output_path = PREVIEW_DIR / f"{output_name}.jpg"

    images = convert_from_path(
        str(pdf_path),
        dpi=150,
        first_page=1,
        last_page=1,
        poppler_path=str(POPPLER_PATH)
    )

    images[0].save(
        output_path,
        "JPEG",
        quality=10,
        optimize=True,
        progressive=True
    )

    return str(output_path)
