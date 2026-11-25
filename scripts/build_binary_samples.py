"""Write PDF, DOCX, and PNG fixtures from the seeded invoice text."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from PIL import Image, ImageDraw, ImageFont

SAMPLES = Path(__file__).resolve().parents[1] / "api" / "samples"
INVOICE = (SAMPLES / "northwind-invoice.txt").read_text(encoding="utf-8")


def write_pdf(text: str, dest: Path) -> None:
    lines = text.splitlines() or [""]
    commands = ["BT", "/F1 11 Tf", "50 760 Td", "14 TL"]
    for index, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index == 0:
            commands.append(f"({escaped}) Tj")
        else:
            commands.append(f"T* ({escaped}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in chunks))
        chunks.append(f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n")
    xref_at = sum(len(part) for part in chunks)
    xref = [f"xref\n0 {len(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    ).encode("ascii")
    dest.write_bytes(b"".join(chunks + xref + [trailer]))


def write_docx(text: str, dest: Path) -> None:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    document.save(dest)


def write_receipt(dest: Path) -> None:
    image = Image.new("RGB", (1100, 420), "white")
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 36) if Path(font_path).exists() else ImageFont.load_default()
    draw.multiline_text(
        (40, 36),
        "RECEIPT\nCafe Atlas\nDate: 2 January 2026\nName: Amal Benyoussef\nTotal due: 86.00 MAD",
        fill="black",
        font=font,
        spacing=12,
    )
    image.save(dest, "PNG")


def main() -> None:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    write_pdf(INVOICE, SAMPLES / "northwind-invoice.pdf")
    write_docx(INVOICE, SAMPLES / "northwind-invoice.docx")
    write_receipt(SAMPLES / "cafe-atlas-receipt.png")
    print("wrote binary samples")


if __name__ == "__main__":
    main()
