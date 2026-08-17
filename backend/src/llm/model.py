"""
Wraps the two model calls the app needs:

  - embed_texts(): Voyage AI embeddings using voyage-code-3
  - answer_with_context(): Gemini LLM grounded in retrieved code chunks
    with inline file:line citations
"""

import os
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from google import genai

load_dotenv()


# ------------------------------------------------------------------
# Gemini configuration
# ------------------------------------------------------------------

GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)

_gemini_client: genai.Client | None = None


def _get_gemini_client() -> genai.Client:
    global _gemini_client

    if _gemini_client is None:

        key = os.environ.get("GEMINI_API_KEY")

        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set — "
                "add it to backend/.env"
            )

        _gemini_client = genai.Client(
            api_key=key
        )

    return _gemini_client


# ------------------------------------------------------------------
# System prompt
# ------------------------------------------------------------------

SYSTEM_PROMPT = """You are a senior engineer helping a developer understand and debug an unfamiliar codebase.

You will be given:
1. A question about the codebase
2. Relevant code chunks retrieved from the repository, each tagged with its file path and line range

Rules:
- Ground every claim in the provided chunks.
- Cite file paths and line numbers inline, like (src/foo.py:42-58).
- If the retrieved chunks don't contain enough information to answer confidently, say so explicitly rather than guessing.
- When tracing call flow or dependencies, be precise about direction (who calls whom).
- Keep answers concise and engineer-to-engineer in tone — no fluff.
"""


# ------------------------------------------------------------------
# Retrieved chunk
# ------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str | None = None


# ------------------------------------------------------------------
# Voyage AI Embeddings
# ------------------------------------------------------------------

def embed_texts(
    texts: list[str],
) -> list[list[float]]:
    """Embed a batch of texts via Voyage AI's code-tuned model."""

    voyage_key = os.environ.get("VOYAGE_API_KEY")

    if not voyage_key:
        raise RuntimeError(
            "VOYAGE_API_KEY is not set — "
            "add it to backend/.env"
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

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                wait_time = (
                    float(retry_after)
                    if retry_after
                    else delay
                )

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


# ------------------------------------------------------------------
# Gemini Answer Generation
# ------------------------------------------------------------------

def answer_with_context(
    question: str,
    chunks: list[RetrievedChunk],
) -> str:

    client = _get_gemini_client()

    context = "\n\n".join(
        f"--- {c.file_path}:{c.start_line}-{c.end_line}"
        f"{f' ({c.symbol_name})' if c.symbol_name else ''} ---\n"
        f"{c.content}"
        for c in chunks
    )

    prompt = f"""
{SYSTEM_PROMPT}

Question:
{question}

Retrieved code context:

{context}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text or ""