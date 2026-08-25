from langchain_core.documents import Document

from app.core.rag_chain import extract_text, format_context


def test_extract_text_from_plain_string():
    assert extract_text("resposta direta") == "resposta direta"


def test_extract_text_from_content_blocks_with_thinking():
    content = [
        {"type": "thinking", "thinking": "raciocínio interno...", "signature": "abc"},
        {"type": "text", "text": "resposta final ao usuário"},
    ]
    assert extract_text(content) == "resposta final ao usuário"


def test_extract_text_joins_multiple_text_blocks():
    content = [
        {"type": "text", "text": "parte 1"},
        {"type": "text", "text": "parte 2"},
    ]
    assert extract_text(content) == "parte 1\nparte 2"


def test_format_context_includes_titulo_as_citation_marker():
    docs = [
        Document(page_content="conteúdo do protocolo A", metadata={"titulo": "Protocolo A"}),
        Document(page_content="conteúdo do protocolo B", metadata={"titulo": "Protocolo B"}),
    ]
    context = format_context(docs)
    assert "[Protocolo A]" in context
    assert "[Protocolo B]" in context
    assert "conteúdo do protocolo A" in context
    assert "conteúdo do protocolo B" in context


def test_format_context_falls_back_to_source_id_when_no_titulo():
    docs = [Document(page_content="texto", metadata={"source_id": "sepse"})]
    context = format_context(docs)
    assert "[sepse]" in context


def test_format_context_empty_list_returns_empty_string():
    assert format_context([]) == ""
