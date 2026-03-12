from pathlib import Path

from pypdf import PdfReader


def parse_uploaded_file(file_path: Path, original_name: str | None = None) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    raise ValueError(f"Unsupported file type for {original_name or file_path.name}")
