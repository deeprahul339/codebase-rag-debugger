"""
Clones a repo, chunks it, embeds the chunks, and stores them in a local
Chroma index. Uses chromadb.PersistentClient, which is fully embedded
(writes to a local folder as SQLite + files) — no server process, no
Docker, nothing to run in the background.
"""
 
import os ##folders, environment variables, file paths
import re ##convert url into safe ID's
import subprocess ##runs commands on machine i.e. running git clone
import threading ##lock to serialise all Chroma access
import time ##pause between batches of api calls

import chromadb  ##local vector store(database)

from .file_scanner import scan_repository
from .code_chunker import chunk_repository, CodeChunk
from ..llm.model import embed_texts

from typing import Any

WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "./.workspace")
INDEX_DIR = os.environ.get("INDEX_DIR", "./.chroma")

_chroma_client: Any = None
# Serialise *all* Chroma access.  chromadb.PersistentClient uses SQLite
# under the hood; concurrent writes (or a write + init) from different
# threads deadlock without an explicit lock at our layer.
_chroma_lock = threading.Lock()


def _get_chroma_client() -> Any:
    """Return the shared Chroma client, creating it on first call (thread-safe)."""
    global _chroma_client
    if _chroma_client is None:  # fast path – no lock needed for reads after init
        with _chroma_lock:
            if _chroma_client is None:  # double-checked locking
                os.makedirs(INDEX_DIR, exist_ok=True)
                _chroma_client = chromadb.PersistentClient(path=INDEX_DIR)
    return _chroma_client


def init_chroma() -> None:
    """Eagerly initialise the Chroma client at server startup.

    Calling this once from the FastAPI lifespan (or at module import time)
    ensures that the first real request never pays the SQLite-open cost and,
    more importantly, that the client is never created from two threads
    simultaneously.
    """
    _get_chroma_client()


def repo_id_from_url(repo_url: str) -> str:
    stripped = re.sub(r"^https?://", "", repo_url)
    return re.sub(r"[^a-zA-Z0-9]", "-", stripped).lower()


def get_or_create_collection(repo_id: str):
    with _chroma_lock:
        return _get_chroma_client().get_or_create_collection(name=f"repo_{repo_id}")


def is_repo_indexed(repo_id: str) -> bool:
    """Returns True if the Chroma collection for this repo already has embeddings."""
    try:
        with _chroma_lock:
            client = _get_chroma_client()
            collection = client.get_collection(name=f"repo_{repo_id}")
            count = collection.count()
        return count > 0
    except Exception:
        return False


def index_repository(repo_url: str) -> dict:
    repo_id = repo_id_from_url(repo_url)
    local_path = os.path.join(WORKSPACE_DIR, repo_id)

    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    # ── Fast-path: already indexed ──────────────────────────────────────────
    # If the Chroma collection exists and already has documents, skip the
    # expensive clone + embed pipeline entirely and return immediately.
    if is_repo_indexed(repo_id):
        collection = get_or_create_collection(repo_id)
        chunk_count = collection.count()
        files = scan_repository(local_path) if os.path.exists(local_path) else []
        print(f"[indexer] '{repo_id}' already indexed ({chunk_count} chunks). Skipping.")
        return {"repoId": repo_id, "fileCount": len(files), "chunkCount": chunk_count, "alreadyIndexed": True}
    # ────────────────────────────────────────────────────────────────────────

    if not os.path.exists(local_path):
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, local_path],## Why --depth 1? It performs a shallow clone.You don't need the entire Git history for RAG.You only need the current source code.
            check=True,
        )

    files = scan_repository(local_path)
    chunks: list[CodeChunk] = chunk_repository(files)
    collection = get_or_create_collection(repo_id)

    # Batch embed + upsert. Voyage AI accepts a batch per request; keep
    # batches modest to stay well under any request-size limits.
    BATCH_SIZE = 128
    for i in range(0, len(chunks), BATCH_SIZE):
        if i > 0:
            time.sleep(0.5)
        batch = chunks[i : i + BATCH_SIZE]
        embeddings = embed_texts([c.content for c in batch])

        collection.upsert(
            ids=[c.id for c in batch],
            embeddings=embeddings,
            documents=[c.content for c in batch],
            metadatas=[
                {
                    "filePath": c.file_path,
                    "startLine": c.start_line,
                    "endLine": c.end_line,
                    "symbolName": c.symbol_name or "",
                    "symbolType": c.symbol_type,
                    "language": c.language,
                }
                for c in batch
            ],
        )

    return {"repoId": repo_id, "fileCount": len(files), "chunkCount": len(chunks)}
