"""Ingestão dos dois índices vetoriais (seção 2.2 do documento de arquitetura):

- **Índice estático**: protocolos institucionais (e, no futuro, conhecimento
  médico geral via PubMedQA/MedQuAD — ainda não integrado). Cresce via
  `add_static_document`, chamado pela aba de upload de protocolo no Streamlit.
- **Índice dinâmico**: prontuários de pacientes, alimentado em tempo real via
  upload no Streamlit (`add_patient_document`), consultado por paciente
  (`get_patient_record`) pelo fluxo LangGraph.
"""

import json
import re
from pathlib import Path

from langchain_classic.retrievers import EnsembleRetriever
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings

from finetuning.data_prep.anonymize import anonymize_text

ROOT = Path(__file__).resolve().parents[2]
PROTOCOLOS_PATH = ROOT / "data" / "raw" / "protocolos.jsonl"
STATIC_STORE_DIR = ROOT / "data" / "vectorstore" / "static"
DYNAMIC_STORE_DIR = ROOT / "data" / "vectorstore" / "dynamic"

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


def add_static_document(titulo: str, texto: str, especialidade: str = "Geral") -> str:
    """Adiciona um novo documento ao índice estático (upload de protocolo).

    Anonimiza como rede de segurança, grava em data/raw/protocolos.jsonl (pra
    o BM25 — que relê o arquivo a cada consulta — enxergar o documento também)
    e insere no Chroma. Retorna o source_id gerado.
    """
    texto, _ = anonymize_text(texto)
    source_id = re.sub(r"[^a-z0-9]+", "_", titulo.lower()).strip("_") or "protocolo_sem_titulo"

    row = {"id": source_id, "titulo": titulo, "especialidade": especialidade, "texto": texto}
    with PROTOCOLOS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    doc = Document(
        page_content=texto,
        metadata={
            "source_type": "protocolo_institucional",
            "source_id": source_id,
            "titulo": titulo,
            "especialidade": especialidade,
        },
    )
    get_static_store().add_documents([doc])
    return source_id


def get_dynamic_store() -> Chroma:
    DYNAMIC_STORE_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma(
        embedding_function=get_embeddings(),
        persist_directory=str(DYNAMIC_STORE_DIR),
        collection_name="dynamic_hvn",
    )


def add_patient_document(
    patient_id: str,
    nome: str,
    texto: str,
    exame_pendente: bool,
    exame_pendente_desc: str | None = None,
) -> None:
    """Indexa um novo prontuário no índice dinâmico (upload de prontuário)."""
    texto, _ = anonymize_text(texto)
    doc = Document(
        page_content=texto,
        metadata={
            "source_type": "prontuario_dinamico",
            "patient_id": patient_id,
            "nome": nome,
            "exame_pendente": exame_pendente,
            "exame_pendente_desc": exame_pendente_desc or "",
        },
    )
    get_dynamic_store().add_documents([doc])


def get_patient_record(patient_id: str) -> dict | None:
    """Busca exata por paciente no índice dinâmico (não é busca semântica —
    usa filtro de metadado, já que queremos o(s) prontuário(s) daquele
    paciente específico, não os "mais parecidos")."""
    result = get_dynamic_store().get(where={"patient_id": patient_id})
    if not result["ids"]:
        return None
    idx = -1  # último prontuário indexado para esse paciente
    metadata = result["metadatas"][idx]
    return {
        "nome": metadata.get("nome", patient_id),
        "prontuario": result["documents"][idx],
        "exame_pendente": bool(metadata.get("exame_pendente", False)),
        "exame_pendente_desc": metadata.get("exame_pendente_desc") or None,
    }


def get_dynamic_retriever(patient_id: str, k: int = 3) -> BaseRetriever:
    """Busca semântica dentro dos prontuários de UM paciente (útil quando há
    várias notas acumuladas ao longo do tempo)."""
    store = get_dynamic_store()
    return store.as_retriever(search_kwargs={"k": k, "filter": {"patient_id": patient_id}})


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
