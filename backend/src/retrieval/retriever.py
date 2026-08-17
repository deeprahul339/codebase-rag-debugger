from ..llm.model import embed_texts, RetrievedChunk
from ..ingestion.indexer import get_vector_store


def retrieve_relevant_chunks(
    repo_id: str,
    query: str,
    top_k: int = 8,
) -> list[RetrievedChunk]:
    """
    Retrieve the most relevant code chunks from the repository's
    FAISS vector index.
    """

    print(">>> retrieve_relevant_chunks() called")
    print(">>> repo_id:", repo_id)
    print(">>> query:", query)

    # Get the FAISS vector store for this repository.
    store = get_vector_store(repo_id)

    print(">>> FAISS vector count:", store.count())

    # No vectors available.
    if store.count() == 0:
        print(">>> No vectors found for repository")
        return []

    # Convert the user's question into an embedding.
    print(">>> Embedding query...")

    [query_embedding] = embed_texts([query])

    print(">>> Query embedding generated")

    # Search the FAISS index.
    print(">>> Searching FAISS...")

    results = store.search(
        embedding=query_embedding,
        k=top_k,
    )

    print(">>> FAISS results:", len(results))

    chunks: list[RetrievedChunk] = []

    for result in results:
        metadata = result["metadata"]

        print(
            ">>> Retrieved:",
            metadata.get("filePath"),
            metadata.get("startLine"),
            metadata.get("endLine"),
            metadata.get("symbolName"),
        )

        chunks.append(
            RetrievedChunk(
                content=str(
                    metadata.get(
                        "content",
                        "",
                    )
                ),
                file_path=str(
                    metadata.get(
                        "filePath",
                        "unknown",
                    )
                ),
                start_line=int(
                    metadata.get(
                        "startLine",
                        0,
                    )
                ),
                end_line=int(
                    metadata.get(
                        "endLine",
                        0,
                    )
                ),
                symbol_name=(
                    str(
                        metadata["symbolName"]
                    )
                    if metadata.get("symbolName")
                    else None
                ),
            )
        )

    print(
        ">>> Retrieved chunks:",
        len(chunks),
    )

    return chunks