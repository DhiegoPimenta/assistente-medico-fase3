"""Ingestão do índice estático (protocolos institucionais) no Chroma.

O índice estático reúne conhecimento institucional (protocolos do Hospital Vida
Nova) e, no futuro, conhecimento médico geral (PubMedQA/MedQuAD — ainda não
integrado). O índice dinâmico (prontuários de pacientes, por upload) é tratado
à parte, com filtro por paciente — ver app/core/rag_chain.py.
"""

import re
from pathlib import Path

from langchain_classic.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings

ROOT = Path(__file__).resolve().parents[2]
PROTOCOLOS_PATH = ROOT / "data" / "raw" / "protocolos.jsonl"
STATIC_STORE_DIR = ROOT / "data" / "vectorstore" / "static"

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def _load_protocolos() -> list[Document]:
    import json

    docs = []
    with open(PROTOCOLOS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            docs.append(
                Document(
                    page_content=row["texto"],
                    metadata={
                        "source_type": "protocolo_institucional",
                        "source_id": row["id"],
                        "titulo": row["titulo"],
                        "especialidade": row["especialidade"],
                    },
                )
            )
    return docs


def build_static_index() -> Chroma:
    """(Re)constrói o índice estático a partir de data/raw/protocolos.jsonl."""
    docs = _load_protocolos()
    STATIC_STORE_DIR.mkdir(parents=True, exist_ok=True)
    store = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        persist_directory=str(STATIC_STORE_DIR),
        collection_name="static_hvn",
    )
    print(f"Índice estático construído com {len(docs)} documentos em {STATIC_STORE_DIR}")
    return store


def get_static_store() -> Chroma:
    return Chroma(
        embedding_function=get_embeddings(),
        persist_directory=str(STATIC_STORE_DIR),
        collection_name="static_hvn",
    )


def get_static_retriever(k: int = 3) -> BaseRetriever:
    """Retriever híbrido (BM25 + busca vetorial) sobre o índice estático.

    O embedding multilíngue usado (MiniLM) tem dificuldade com siglas clínicas
    em português — ex.: a query "AVC agudo" rankeava o próprio protocolo de AVC
    em último lugar entre 8 documentos, enquanto "acidente vascular cerebral"
    (por extenso) o rankeava em primeiro. BM25 cobre exatamente esse caso de
    correspondência exata de sigla/termo, complementando a busca semântica.
    """
    docs = _load_protocolos()
    bm25 = BM25Retriever.from_documents(
        docs, preprocess_func=lambda text: re.findall(r"\w+", text.lower())
    )
    bm25.k = k

    vector_retriever = get_static_store().as_retriever(search_kwargs={"k": k})

    return EnsembleRetriever(retrievers=[bm25, vector_retriever], weights=[0.5, 0.5])


if __name__ == "__main__":
    build_static_index()
