import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()  # must run before importing modules that read env vars at import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.routes import repository, chat
from src.ingestion.indexer import init_chroma


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eagerly open the Chroma SQLite connection before the first request.

    init_chroma() is blocking I/O (SQLite open + WAL setup), so we run it
    in the default thread executor to avoid freezing the event loop.
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, init_chroma)
    yield


app = FastAPI(title="Codebase RAG Debugger API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deploying anywhere real
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(repository.router)
app.include_router(chat.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        timeout_keep_alive=600,  # 10 min — allows long indexing jobs to complete
    )
