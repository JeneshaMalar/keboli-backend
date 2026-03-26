"""File text extraction utilities for PDF and DOCX documents."""

import io

import fitz
from docx import Document


async def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Extract text from a file based on its extension.

    Supports PDF and DOCX formats; falls back to UTF-8 decoding for
    other file types.

    Args:
        file_content: Raw binary content of the uploaded file.
        filename: Original filename used to determine the extraction strategy.

    Returns:
        Extracted text content as a string.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        doc = fitz.open(stream=file_content, filetype="pdf")
        return "".join([page.get_text() for page in doc])

    if lower.endswith(".docx"):
        doc = Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])

    return file_content.decode("utf-8")
