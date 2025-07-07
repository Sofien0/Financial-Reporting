import os
from pathlib import Path
import pdfplumber

PDF_ROOT = Path("data/raw")
OUT_DIR = Path("data/processed/parsed_text")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_pdf_text(pdf_path: Path) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        print(f"[!] Failed to parse {pdf_path.name}: {e}")
        return ""

def save_text_for_pdf(pdf_path: Path):
    relative_name = pdf_path.stem.replace(" ", "_").replace("__", "_")
    output_file = OUT_DIR / f"{relative_name}.txt"
    if output_file.exists():
        print(f"[✓] Already parsed: {output_file.name}")
        return
    text = parse_pdf_text(pdf_path)
    if text.strip():
        output_file.write_text(text, encoding="utf-8")
        print(f"[✔] Saved text: {output_file.name}")
    else:
        print(f"[!] Empty text extracted: {pdf_path.name}")

def parse_all_pdfs(limit=None):
    print("🔍 Scanning for PDF files...")
    count = 0
    for root, dirs, files in os.walk(PDF_ROOT):
        for file in files:
            if file.endswith(".pdf"):
                pdf_path = Path(root) / file
                save_text_for_pdf(pdf_path)
                count += 1
                if limit is not None and count >= limit:  # only process a few for testing
                    return

if __name__ == "__main__":
    parse_all_pdfs(limit=None)  # Change limit as needed
