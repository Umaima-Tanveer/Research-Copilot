import fitz
import os
import json

UPLOAD_FOLDER = "uploads/Run7"
OUTPUT_FILE = "output/Run7/extracted_papers.json"


def extract_text_from_pdf(pdf_path):
    try:
        document = fitz.open(pdf_path)
        text = ""

        for page in document:
            text += page.get_text("text") + "\n"

        document.close()
        return text

    except Exception as e:
        print(f"Error reading {pdf_path}")
        print(e)
        return ""


def process_all_pdfs():
    papers = []

    if not os.path.exists(UPLOAD_FOLDER):
        print("Uploads folder not found")
        return []

    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found")
        return []

    print(f"Found {len(pdf_files)} PDFs")

    for idx, file in enumerate(pdf_files, 1):
        path = os.path.join(UPLOAD_FOLDER, file)

        print(f"Processing {file}")

        text = extract_text_from_pdf(path)

        papers.append({
            "paper_id": idx,
            "filename": file,
            "text": text
        })

        print(f"Extracted {len(text)} chars")

    return papers


def save_papers_json(papers):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=4, ensure_ascii=False)

    print(f"Saved {len(papers)} papers")


if __name__ == "__main__":
    papers = process_all_pdfs()
    if papers:
        save_papers_json(papers)