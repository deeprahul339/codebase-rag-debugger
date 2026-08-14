"""
Wraps the two model calls the app needs:
  - embed_texts(): Voyage AI embeddings (there's no first-party embeddings
    endpoint from Groq or Anthropic, so this uses Voyage's code-tuned model)
  - answer_with_context(): Groq-hosted LLM, grounded in retrieved code
    chunks, with inline file:line citations
"""

import os
from dataclasses import dataclass

import httpx
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
_groq_client: Groq | None = None


def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        key = os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is not set — add it to backend/.env")
        _groq_client = Groq(api_key=key)
    return _groq_client

SYSTEM_PROMPT = """You are a senior engineer helping a developer understand and debug an unfamiliar codebase.

You will be given:
1. A question about the codebase
2. Relevant code chunks retrieved from the repository, each tagged with its file path and line range

Rules:
- Ground every claim in the provided chunks. Cite file paths and line numbers inline, like (src/foo.py:42-58).
- If the retrieved chunks don't contain enough information to answer confidently, say so explicitly rather than guessing.
- When tracing call flow or dependencies, be precise about direction (who calls whom).
- Keep answers concise and engineer-to-engineer in tone — no fluff."""


@dataclass
class RetrievedChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str | None = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts via Voyage AI's code-tuned model."""

    voyage_key = os.environ.get("VOYAGE_API_KEY")

    if not voyage_key:
        raise RuntimeError(
            "VOYAGE_API_KEY is not set — add it to backend/.env"
        )

    max_retries = 5
    delay = 3.0

    for attempt in range(max_retries):
        response = httpx.post(
            "https://api.voyageai.com/v1/embeddings",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {voyage_key}",
            },
            json={
                "input": texts,
                "model": "voyage-code-3",
            },
            timeout=60.0,
        )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")

            try:
                wait_time = float(retry_after) if retry_after else delay
            except ValueError:
                wait_time = delay

            print(
                f"Voyage AI rate limit. "
                f"Retrying in {wait_time}s "
                f"(attempt {attempt + 1}/{max_retries})"
            )

            time.sleep(wait_time)
            delay *= 2
            continue

        response.raise_for_status()

        data = response.json()

        return [
            item["embedding"]
            for item in data["data"]
        ]

    raise RuntimeError(
        "Voyage AI embedding request failed after "
        f"{max_retries} attempts."
    )


def answer_with_context(question: str, chunks: list[RetrievedChunk]) -> str:
    client = _get_groq_client()

    context = "\n\n".join(
        f"--- {c.file_path}:{c.start_line}-{c.end_line}"
        f"{f' ({c.symbol_name})' if c.symbol_name else ''} ---\n{c.content}"
        for c in chunks
    )

    # Groq's SDK is OpenAI-compatible: chat.completions.create with a
    # messages list (system role included), not Anthropic's messages.create
    # with a separate `system` param.
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nRetrieved code context:\n\n{context}",
            },
        ],
    )

    return response.choices[0].message.content or ""
