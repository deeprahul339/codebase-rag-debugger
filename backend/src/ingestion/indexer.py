"""
Clones a repository, chunks its source code, generates embeddings,
and stores the vectors + metadata in a local FAISS index.

FAISS is persisted locally through FAISSVectorStore.
"""

import os
import re
import subprocess #used to execute system commands e.g. git clone command
import time

from .file_scanner import scan_repository
from .code_chunker import chunk_repository, CodeChunk
from ..llm.model import embed_texts
from .vector_store import FAISSVectorStore


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BACKEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


def _resolve_project_path(
    env_name: str,
    default_rel_path: str,
) -> str:
    """
    Resolve a path relative to the backend directory.

    Example:
        FAISS_DIR=.faiss

    becomes:
        <backend>/.faiss
    """

    value = os.environ.get(env_name)

    if value is None:
        return os.path.abspath(
            os.path.join(BACKEND_DIR, default_rel_path)
        )

    if os.path.isabs(value):
        return value

    return os.path.abspath(
        os.path.join(BACKEND_DIR, value)
    )


WORKSPACE_DIR = _resolve_project_path(
    "WORKSPACE_DIR",
    ".workspace",
)

FAISS_DIR = _resolve_project_path(
    "FAISS_DIR",
    ".faiss",
)


# ---------------------------------------------------------------------------
# FAISS vector store
# ---------------------------------------------------------------------------

def get_vector_store(repo_id: str) -> FAISSVectorStore:
    """
    Return the FAISS vector store for a repository.

    Each repository gets its own FAISS collection/index.
    """

    return FAISSVectorStore(
        index_dir=FAISS_DIR,
        collection_name=f"repo_{repo_id}",
    )


# ---------------------------------------------------------------------------
# Repository ID
# ---------------------------------------------------------------------------

def repo_id_from_url(repo_url: str) -> str:
    """
    Convert a repository URL into a filesystem/index-safe ID.

    Example:

        https://github.com/user/my-repo

    becomes:

        github-com-user-my-repo
    """

    stripped = re.sub(
        r"^https?://",
        "",
        repo_url,
    )

    return re.sub(
        r"[^a-zA-Z0-9]",
        "-",
        stripped,
    ).lower()


# ---------------------------------------------------------------------------
# Check whether repository is already indexed
# ---------------------------------------------------------------------------

def is_repo_indexed(repo_id: str) -> bool:
    """
    Check whether the repository already has vectors in FAISS.
    """
    try:
        store = get_vector_store(repo_id)

        count = store.count()

        print(">>> FAISS vector count:", count)

        return count > 0

    except Exception as exc:
        print("!!! ERROR in is_repo_indexed !!!")
        print("!!! TYPE:", type(exc).__name__)
        print("!!! ERROR:", repr(exc))


        return False


def get_repo_index_status(repo_id: str) -> dict:
    """
    Return indexing status and statistics for a repository.
    """

    local_path = os.path.join(
        WORKSPACE_DIR,
        repo_id,
    )

    indexed = is_repo_indexed(repo_id)

    if not indexed:
        return {
            "indexed": False,
            "fileCount": 0,
            "chunkCount": 0,
        }

    # Get the existing FAISS vector store
    store = get_vector_store(repo_id)

    # Each vector represents one code chunk
    chunk_count = store.count()

    # Scan repository to count files
    files = (
        scan_repository(local_path)
        if os.path.exists(local_path)
        else []
    )

    return {
        "indexed": True,
        "fileCount": len(files),
        "chunkCount": chunk_count,
    }

# ---------------------------------------------------------------------------
# Index repository
# ---------------------------------------------------------------------------

def index_repository(repo_url: str) -> dict:
    """
    Clone a repository, scan files, chunk code, generate embeddings,
    and store everything in FAISS.
    """

    repo_id = repo_id_from_url(repo_url)

    local_path = os.path.join(
        WORKSPACE_DIR,
        repo_id,
    )

    os.makedirs(
        WORKSPACE_DIR,
        exist_ok=True,
    )

    # -----------------------------------------------------------------------
    # Fast path: repository already indexed
    # -----------------------------------------------------------------------

    if is_repo_indexed(repo_id):

        store = get_vector_store(repo_id)

        chunk_count = store.count()

        files = (
            scan_repository(local_path)
            if os.path.exists(local_path)
            else []
        )

        return {
            "repoId": repo_id,
            "fileCount": len(files),
            "chunkCount": chunk_count,
            "alreadyIndexed": True,
        }

    # -----------------------------------------------------------------------
    # Clone repository
    # -----------------------------------------------------------------------

    if not os.path.exists(local_path):

        print(">>> Repository doesn't exist locally")
        print(">>> Starting git clone...")

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repo_url,
                local_path,
            ],
            check=True,
        )

        print(">>> Git clone completed")

    else:
        print(">>> Repository already exists locally")
        print(">>> Skipping git clone")

    print(">>> local_path:", local_path)

    # -----------------------------------------------------------------------
    # Scan repository
    # -----------------------------------------------------------------------

    print(">>> Starting scan_repository()...")

    files = scan_repository(local_path)

    print(">>> scan_repository() completed")
    print(">>> Number of files:", len(files))

    # -----------------------------------------------------------------------
    # Chunk repository
    # -----------------------------------------------------------------------

    print(">>> Starting chunk_repository()...")

    chunks: list[CodeChunk] = chunk_repository(files)

    print(">>> chunk_repository() completed")
    print(">>> Number of chunks:", len(chunks))

    if not chunks:
        print("!!! No code chunks found")

        return {
            "repoId": repo_id,
            "fileCount": len(files),
            "chunkCount": 0,
            "alreadyIndexed": False,
        }

    # -----------------------------------------------------------------------
    # Get FAISS store
    # -----------------------------------------------------------------------

    print(">>> Getting FAISS vector store...")

    store = get_vector_store(repo_id)

    print(">>> FAISS vector store obtained")
    print(">>> Store:", store)

    # -----------------------------------------------------------------------
    # Batch embedding + FAISS insertion
    # -----------------------------------------------------------------------

    BATCH_SIZE = 128

    for i in range(
        0,
        len(chunks),
        BATCH_SIZE,
    ):

        print(
            f">>> Starting batch: "
            f"{i} to {min(i + BATCH_SIZE, len(chunks))}"
        )

        if i > 0:
            print(">>> Sleeping 0.5 seconds...")
            time.sleep(0.5)

        batch = chunks[
            i : i + BATCH_SIZE
        ]

        print(">>> Batch size:", len(batch))

        # ---------------------------------------------------------------
        # Generate embeddings
        # ---------------------------------------------------------------

        print(">>> Calling embed_texts()...")

        embeddings = embed_texts(
            [
                chunk.content
                for chunk in batch
            ]
        )

        print(">>> embed_texts() completed")
        print(
            ">>> Number of embeddings:",
            len(embeddings),
        )

        # ---------------------------------------------------------------
        # Build metadata
        # ---------------------------------------------------------------

        metadata = [
            {
                "id": chunk.id,
                "filePath": chunk.file_path,
                "startLine": chunk.start_line,
                "endLine": chunk.end_line,
                "symbolName": (
                    chunk.symbol_name
                    or ""
                ),
                "symbolType": chunk.symbol_type,
                "language": chunk.language,
                "content": chunk.content,
            }
            for chunk in batch
        ]

        # ---------------------------------------------------------------
        # Add vectors + metadata to FAISS
        # ---------------------------------------------------------------

        print(">>> Calling FAISS add()...")

        store.add(
            embeddings=embeddings,
            metadata=metadata,
        )

        print(">>> FAISS add() completed")

    # -----------------------------------------------------------------------
    # Final result
    # -----------------------------------------------------------------------

    final_count = store.count()

    print("========================================")
    print(">>> Repository indexing completed")
    print(">>> repo_id:", repo_id)
    print(">>> files:", len(files))
    print(">>> chunks:", len(chunks))
    print(">>> FAISS vectors:", final_count)
    print("========================================")

    return {
        "repoId": repo_id,
        "fileCount": len(files),
        "chunkCount": len(chunks),
        "alreadyIndexed": False,
    }