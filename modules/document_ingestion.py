
import json
from pathlib import Path
from pypdf import PdfReader

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "threats.json"
)


def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)

    return "\n".join(pages)


def add_document(title, content, category="Uploaded Document"):
    if not content.strip():
        return False

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        records = json.load(file)

    records.append({
        "id": "DOC" + str(len(records) + 1).zfill(3),
        "title": title,
        "content": content[:15000],
        "category": category,
        "source": "User Uploaded Document"
    })

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=4)

    return True
