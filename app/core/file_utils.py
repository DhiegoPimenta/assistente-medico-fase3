"""Extração de texto de arquivos enviados via upload no Streamlit (.txt/.pdf)."""


def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return uploaded_file.read().decode("utf-8", errors="ignore")
