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
    Core RAG loop:
    1. Retrieve relevant code chunks from the FAISS index.
    2. Send the retrieved chunks to the LLM.
    3. Return the generated answer and source information.
    """

    if not body.repoId or not body.question:
        raise HTTPException(
            status_code=400,
            detail="repoId and question are required",
        )

    try:
        # Retrieve relevant chunks from the FAISS index
        chunks = retrieve_relevant_chunks(
            body.repoId,
            body.question,
        )

        # Generate an answer using the retrieved code as context
        answer = answer_with_context(
            body.question,
            chunks,
        )

        return {
            "answer": answer,
            "sources": [
                {
                    "filePath": chunk.file_path,
                    "startLine": chunk.start_line,
                    "endLine": chunk.end_line,
                    "symbolName": chunk.symbol_name,
                }
                for chunk in chunks
            ],
        }

    except Exception as exc:
        print(f"Chat query failed: {exc}")

        raise HTTPException(
            status_code=500,
            detail="Failed to answer question",
        ) from exc