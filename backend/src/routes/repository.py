import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..ingestion.indexer import index_repository, is_repo_indexed, repo_id_from_url, WORKSPACE_DIR
import os

router = APIRouter(prefix="/api/repository", tags=["repository"])

# Dedicated thread pool for long-running indexing work so the event loop
# is never blocked by the Voyage AI embedding calls + sleeps.
_index_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="indexer")


class IndexRepoRequest(BaseModel):
    repoUrl: str


@router.post("/check")
async def check_repo(body: IndexRepoRequest):
    print(">>> /check endpoint called")
    print(">>> repoUrl:", body.repoUrl)

    if not body.repoUrl:
        raise HTTPException(status_code=400, detail="repoUrl is required")

    print(">>> Creating repo_id...")
    repo_id = repo_id_from_url(body.repoUrl)
    print(">>> repo_id:", repo_id)

    loop = asyncio.get_running_loop()

    print(">>> Calling is_repo_indexed...")
    indexed = await loop.run_in_executor(
        _index_executor,
        is_repo_indexed,
        repo_id,
    )

    print(">>> is_repo_indexed returned:", indexed)

    return {
        "repoId": repo_id,
        "indexed": indexed,
    }

@router.post("/index")
async def index_repo(body: IndexRepoRequest):
    """
    Clones the repo, chunks it, embeds chunks, and stores them in the
    local Chroma index.

    The heavy lifting (git clone + many sequential Voyage AI API calls with
    sleep() between batches) is intentionally offloaded to a thread-pool
    executor so the FastAPI/uvicorn event loop is never blocked.  Without
    this the server becomes completely unresponsive while indexing, causing
    the frontend to time out showing "Indexing...".

    If the repo is already indexed in Chroma, index_repository returns
    immediately without re-embedding anything.
    """
    if not body.repoUrl:
        raise HTTPException(status_code=400, detail="repoUrl is required")

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _index_executor,
            index_repository,
            body.repoUrl,
        )
        return result
    except Exception as exc:
        print(f"Indexing failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to index repository: {exc}") from exc


@router.get("/status/{repo_id}")
def repo_status(repo_id: str):
    """
    Quick check by repo_id — returns whether a repo is indexed in Chroma.
    """
    local_path = os.path.join(WORKSPACE_DIR, repo_id)
    indexed = is_repo_indexed(repo_id)
    return {"repoId": repo_id, "indexed": indexed, "hasLocalClone": os.path.exists(local_path)}

