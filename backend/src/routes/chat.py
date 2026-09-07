import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agent.agent import run_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    repoId: str
    question: str


@router.post("")
def chat(body: ChatRequest):
    """
    Run the AI debugging agent and stream its events
    back to the frontend.
    """

    if not body.repoId or not body.question:
        raise HTTPException(
            status_code=400,
            detail="repoId and question are required",
        )

    def generate():
        try:
            for event in run_agent(
                body.repoId,
                body.question,
            ):
                yield f"data: {json.dumps(event)}\n\n"

        except Exception as exc:
            print(f"Agent query failed: {exc}")

            error_event = {
                "type": "ERROR",
                "message": "Failed to process question",
            }

            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )