import pytest
from pypdf.errors import PdfReadError

from worker.parser import extract_text_from_pdf

SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /Resources <</Font <</F1 4 0 R>>>> "
    b"/MediaBox [0 0 612 792] /Contents 5 0 R>> endobj\n"
    b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
    b"5 0 obj <</Length 120>> stream\n"
    b"BT\n/F1 12 Tf\n100 700 Td\n(Jane Doe) Tj\n0 -20 Td\n(Experience) Tj\n"
    b"0 -20 Td\n(Software Engineer at CloudCorp building distributed systems.) Tj\n"
    b"ET\nendstream\nendobj\nxref\n0 6\ntrailer <</Size 6 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
)


def test_extract_text_valid_pdf() -> None:
    text = extract_text_from_pdf(SAMPLE_PDF_BYTES)
    assert "Jane Doe" in text
    assert "CloudCorp" in text


def test_extract_text_empty_bytes() -> None:
    with pytest.raises(ValueError, match="Empty PDF byte stream"):
        extract_text_from_pdf(b"")


def test_extract_text_corrupt_pdf() -> None:
    with pytest.raises((PdfReadError, Exception)):
        extract_text_from_pdf(b"not a real pdf file content")
