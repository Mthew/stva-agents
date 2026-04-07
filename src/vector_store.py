"""
vector_store.py — ChromaDB para indexar y recuperar secciones de UGC/

Fase 1: indexa solo los archivos biométricos de UGC/ (Dante y Valeria).
Los archivos pesan 10-14k tokens cada uno — no son inyectables completos en el prompt.
El RAG recupera solo las secciones relevantes según el query.

Fase 2+: se extiende para indexar también knowledge/ cuando el corpus crezca.
"""

from pathlib import Path
from typing import Optional
import re

import chromadb
from chromadb.utils import embedding_functions

from src.config import UGC_DIR, CHROMA_DIR, VOYAGE_API_KEY


def _get_embedding_function():
    """Retorna la función de embeddings. Usa Voyage AI si hay API key, sino el default de ChromaDB."""
    if VOYAGE_API_KEY:
        return embedding_functions.create_langchain_embedding(
            # Voyage AI via langchain — alternativa: usar voyageai directamente
            # Por simplicidad en Fase 1 usamos el embedding por defecto si no hay Voyage key
        )
    return embedding_functions.DefaultEmbeddingFunction()


def _chunk_markdown_by_section(text: str, source: str) -> list[dict]:
    """
    Divide un documento markdown en chunks por sección (## headers).
    Retorna lista de {id, text, metadata}.
    """
    chunks = []
    sections = re.split(r'\n(?=#{1,3} )', text)

    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        # Extraer el título de la sección para el ID y metadata
        first_line = section.split('\n')[0].strip('#').strip()
        chunk_id = f"{source}__section_{i}__{first_line[:40].replace(' ', '_').lower()}"

        # Extraer persona y file_type del source para filtrado
        parts = source.split("/")
        persona = parts[0] if len(parts) >= 1 else ""
        file_type = parts[1] if len(parts) >= 2 else ""

        chunks.append({
            "id": chunk_id,
            "text": section,
            "metadata": {
                "source": source,
                "persona": persona,       # "dante" | "valeria"
                "file_type": file_type,   # "face" | "body"
                "section_title": first_line,
                "section_index": i,
            }
        })

    return chunks


class UGCVectorStore:
    """
    Vector store ChromaDB para los archivos biométricos de UGC/.
    Permite recuperar secciones específicas de los prompts maestros de Dante y Valeria.
    """

    COLLECTION_NAME = "ugc_biometrics"

    def __init__(self):
        CHROMA_DIR.mkdir(exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self.ef,
        )

    def index_ugc_files(self, force_reindex: bool = False):
        """
        Indexa todos los archivos .md de UGC/ si no están indexados aún.
        force_reindex=True borra y re-indexa todo.
        """
        if force_reindex:
            self.client.delete_collection(self.COLLECTION_NAME)
            self.collection = self.client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self.ef,
            )

        if self.collection.count() > 0 and not force_reindex:
            return  # Ya indexado

        all_ids, all_texts, all_metas = [], [], []

        for md_file in sorted(UGC_DIR.rglob("*.md")):
            # source = "dante/face", "valeria/body", etc.
            relative = md_file.relative_to(UGC_DIR)
            source = str(relative.with_suffix("")).replace("\\", "/")

            text = md_file.read_text(encoding="utf-8")
            chunks = _chunk_markdown_by_section(text, source)

            for chunk in chunks:
                all_ids.append(chunk["id"])
                all_texts.append(chunk["text"])
                all_metas.append(chunk["metadata"])

        if all_ids:
            self.collection.add(
                ids=all_ids,
                documents=all_texts,
                metadatas=all_metas,
            )

    def query(
        self,
        query_text: str,
        persona: Optional[str] = None,
        file_type: Optional[str] = None,
        n_results: int = 4,
    ) -> str:
        """
        Recupera las secciones más relevantes de UGC/ para el query.

        persona: 'dante' | 'valeria' | None (busca en ambos)
        file_type: 'face' | 'body' | None (busca en ambos)
        n_results: número de chunks a recuperar
        """
        if self.collection.count() == 0:
            self.index_ugc_files()

        # Construir filtro de metadata usando campos separados
        where = None
        conditions = []
        if persona:
            conditions.append({"persona": {"$eq": persona}})
        if file_type:
            conditions.append({"file_type": {"$eq": file_type}})

        if len(conditions) == 1:
            where = conditions[0]
        elif len(conditions) > 1:
            where = {"$and": conditions}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count()),
            where=where,
        )

        if not results["documents"] or not results["documents"][0]:
            return ""

        chunks = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source_label = meta.get("source", "")
            section_title = meta.get("section_title", "")
            chunks.append(f"[{source_label} — {section_title}]\n{doc}")

        return "\n\n---\n\n".join(chunks)


# Instancia global (lazy-initialized)
_store: Optional[UGCVectorStore] = None


def get_ugc_store() -> UGCVectorStore:
    """Retorna la instancia global del UGC vector store, inicializándola si es necesario."""
    global _store
    if _store is None:
        _store = UGCVectorStore()
        _store.index_ugc_files()
    return _store


def query_ugc(
    query: str,
    persona: Optional[str] = None,
    file_type: Optional[str] = None,
    n_results: int = 4,
) -> str:
    """Shortcut para hacer queries al UGC store."""
    return get_ugc_store().query(query, persona=persona, file_type=file_type, n_results=n_results)
