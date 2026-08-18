from src.retrieval.reranker import rerank_results
from ..retrieval.retriever import retrieve_relevant_chunks


def detect_intent(query: str) -> str:
    q = query.lower()

    if any(word in q for word in [
        "what does",
        "what is happening",
        "explain",
        "how does",
    ]):
        return "explain"

    if any(word in q for word in [
        "where is",
        "where used",
        "used where",
        "references",
    ]):
        return "usage"

    if any(word in q for word in [
        "break",
        "impact",
        "affected",
    ]):
        return "impact"

    return "general"


def search_code(
    repo_id: str,
    query: str,
    k: int = 5,
) -> list[dict]:
    """Search the indexed repository for code relevant to a query."""

    if not repo_id:
        raise ValueError("Repository ID is required.")

    if not query:
        raise ValueError("Query is required.")

    k = max(1, min(k, 20))

    # Detect what the user is asking
    intent = detect_intent(query)

    # Retrieve more candidates than we finally return
    chunks = retrieve_relevant_chunks(
        repo_id=repo_id,
        query=query,
        top_k=20,
    )

    results = []

    for chunk in chunks:
        results.append({
            "filePath": chunk.file_path,
            "startLine": chunk.start_line,
            "endLine": chunk.end_line,
            "symbolName": chunk.symbol_name,
            "content": chunk.content,
            "score": getattr(chunk, "score", 0),
        })

    # Rerank the retrieved candidates
    results = rerank_results(
        query=query,
        results=results,
    )

    # Return only the requested number
    return results[:k]