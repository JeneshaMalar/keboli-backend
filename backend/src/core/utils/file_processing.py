import io

import fitz  
from docx import Document


async def extract_text_from_file(file_content: bytes, filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        doc = fitz.open(stream=file_content, filetype="pdf")
        return "".join([page.get_text() for page in doc])

    if lower.endswith(".docx"):
        doc = Document(io.BytesIO(file_content))
        return "\n".join([para.text for para in doc.paragraphs])

    return file_content.decode("utf-8")
