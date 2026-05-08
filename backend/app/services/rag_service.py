"""
RAGService — document ingestion + retrieval-augmented generation.

Flow:
  ingest_document()  →  chunk → embed (via Anthropic) → store in ChromaDB
  answer_question()  →  embed query → retrieve chunks → ask Claude with context
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import anthropic
from app.config import settings


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    chunks, start = [], 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c for c in chunks if c.strip()]


def _read_file(file_path: str) -> str:
    """Read text from PDF, Markdown, or plain text files."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            raise RuntimeError("Install PyMuPDF: pip install pymupdf")

    # .md, .txt, .rst, etc.
    return path.read_text(encoding="utf-8", errors="replace")


class RAGService:
    def __init__(self):
        self.anthropic = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

        # Persistent ChromaDB client
        self.chroma = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _collection_name(self, project_id: str) -> str:
        return f"project_{project_id.replace('-', '_')}"

    def _get_or_create_collection(self, project_id: str):
        name = self._collection_name(project_id)
        return self.chroma.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    # ──────────────────────────────────────────────────────────────────────
    # Embed a list of texts using Claude's embedding model
    # ──────────────────────────────────────────────────────────────────────
    async def _embed(self, texts: List[str]) -> List[List[float]]:
        """Use voyage-3 through Anthropic-compatible API for embeddings."""
        # ChromaDB's default embedding function works well enough for prototyping.
        # For production, swap with a dedicated embedding model.
        # Here we use chromadb's built-in sentence-transformers embedding.
        # Returned as a list of lists to match chromadb expectations.
        from chromadb.utils import embedding_functions
        ef = embedding_functions.DefaultEmbeddingFunction()
        return ef(texts)

    # ──────────────────────────────────────────────────────────────────────
    # Ingest a document file for a project
    # ──────────────────────────────────────────────────────────────────────
    async def ingest_document(
        self,
        project_id: str,
        file_path: str,
        filename: str,
        doc_id: str,
    ) -> int:
        """Chunk, embed, and store a document. Returns number of chunks stored."""
        raw_text = _read_file(file_path)
        chunks = _chunk_text(raw_text)

        if not chunks:
            return 0

        embeddings = await self._embed(chunks)
        collection = self._get_or_create_collection(project_id)

        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"filename": filename, "doc_id": doc_id, "chunk_index": i}
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    # ──────────────────────────────────────────────────────────────────────
    # Answer a question using RAG
    # ──────────────────────────────────────────────────────────────────────
    async def answer_question(
        self,
        project_id: str,
        question: str,
        conversation_history: Optional[List[dict]] = None,
        top_k: int = 5,
    ) -> dict:
        """
        Retrieve relevant chunks, then ask Claude to answer based on them.
        Returns { answer: str, sources: List[str] }
        """
        collection = self._get_or_create_collection(project_id)

        # Embed the question and retrieve top-k chunks
        q_embedding = (await self._embed([question]))[0]
        results = collection.query(
            query_embeddings=[q_embedding],
            n_results=min(top_k, collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        context_chunks = results["documents"][0] if results["documents"] else []
        source_files = list({
            m["filename"]
            for m in (results["metadatas"][0] if results["metadatas"] else [])
        })

        context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else "No documents found."

        # Build messages for Claude
        system = """\
You are a helpful AI assistant for a project management tool. \
Answer questions about the project based ONLY on the provided context. \
If the context does not contain the answer, say so honestly. \
Cite the source files when relevant.\
"""
        history = conversation_history or []
        messages = history + [
            {
                "role": "user",
                "content": f"""Context from project documents:
\"\"\"
{context_text}
\"\"\"

Question: {question}""",
            }
        ]

        response = await self.anthropic.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=messages,
        )

        return {
            "answer": response.content[0].text,
            "sources": source_files,
            "model": self.model,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Delete all vectors for a document
    # ──────────────────────────────────────────────────────────────────────
    async def delete_document(self, project_id: str, doc_id: str):
        collection = self._get_or_create_collection(project_id)
        # Get all chunk IDs for this document
        results = collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            collection.delete(ids=results["ids"])
