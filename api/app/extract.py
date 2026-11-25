"""Read PDF, image, docx, and text files into page strings."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from PIL import Image
from pypdf import PdfReader

from app.config import MAX_PAGES

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


@dataclass
class Page:
    number: int
    text: str
    ocr: bool


def extract_file(path: Path) -> list[Page]:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return [Page(1, _read_text(path), False)]
    if suffix == ".docx":
        return [Page(1, _read_docx(path), False)]
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix in IMAGE_SUFFIXES:
        return _read_image(path)
    raise ValueError(
        "Unsupported file. Use PDF, PNG, JPEG, TIFF, BMP, WEBP, DOCX, or TXT."
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")


def _read_docx(path: Path) -> str:
    document = Document(str(path))
    parts = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _read_pdf(path: Path) -> list[Page]:
    reader = PdfReader(str(path))
    if len(reader.pages) > MAX_PAGES:
        raise ValueError(f"PDF has too many pages (max {MAX_PAGES})")
    pages: list[Page] = []
    thin: list[tuple[int, int]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").replace("\x00", "").strip()
        pages.append(Page(index, text, False))
        if len(text) < 25:
            thin.append((index, len(pages) - 1))
    if not thin:
        return pages
    raster = _rasterize(path, [number for number, _ in thin])
    from app.ocr import ocr_pil

    for (number, slot), image in zip(thin, raster):
        pages[slot] = Page(number, ocr_pil(image).strip(), True)
    return pages


def _rasterize(path: Path, page_numbers: list[int]):
    try:
        from pdf2image import convert_from_path
    except ImportError as exc:
        raise RuntimeError("pdf2image is not installed, so this scan cannot be read") from exc
    images = []
    for number in page_numbers:
        try:
            batch = convert_from_path(
                str(path),
                dpi=200,
                first_page=number,
                last_page=number,
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not rasterize that PDF. poppler is required for scanned pages."
            ) from exc
        if not batch:
            raise RuntimeError(f"PDF page {number} did not rasterize")
        images.append(batch[0])
    return images


def _read_image(path: Path) -> list[Page]:
    from app.ocr import ocr_file

    with Image.open(path) as image:
        image.verify()
    texts = ocr_file(path)
    return [Page(index, text.strip(), True) for index, text in enumerate(texts, start=1)]
