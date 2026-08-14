from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..retrieval.retriever import retrieve_relevant_chunks
from ..llm.model import answer_with_context

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    repoId: str
    question: str


@router.post("")
def chat(body: ChatRequest):
    """
    Core RAG loop: retrieve relevant chunks -> ask Claude, grounded in
    those chunks -> return the answer + the sources used (for citations
    in the UI, see SourceCard.tsx on the frontend).
    """
    if not body.repoId or not body.question:
        raise HTTPException(status_code=400, detail="repoId and question are required")

    try:
        chunks = retrieve_relevant_chunks(body.repoId, body.question)
        answer = answer_with_context(body.question, chunks)

        return {
            "answer": answer,
            "sources": [
                {
                    "filePath": c.file_path,
                    "startLine": c.start_line,
                    "endLine": c.end_line,
                    "symbolName": c.symbol_name,
                }
                for c in chunks
            ],
        }
    except Exception as exc:
        print(f"Chat query failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to answer question") from exc
