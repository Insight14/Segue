import io
import logging

from pypdf import PdfReader

logger = logging.getLogger("convo-glasses-parser")


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: int = 20) -> str:
    """Extract and normalize plain text from PDF bytes using pypdf."""
    if not pdf_bytes:
        raise ValueError("Empty PDF byte stream received")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(reader.pages)
    if num_pages == 0:
        raise ValueError("PDF has 0 pages")

    pages_to_read = min(num_pages, max_pages)
    text_chunks: list[str] = []

    for idx in range(pages_to_read):
        page = reader.pages[idx]
        extracted = page.extract_text()
        if extracted:
            text_chunks.append(extracted.strip())

    full_text = "\n\n".join(text_chunks).strip()
    if not full_text:
        raise ValueError(
            "Could not extract any readable text from PDF (it may be scanned/image-only)"
        )

    return full_text
