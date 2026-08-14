from ..llm.model import embed_texts, RetrievedChunk
from ..ingestion.indexer import get_or_create_collection


def retrieve_relevant_chunks(repo_id: str, query: str, top_k: int = 8) -> list[RetrievedChunk]:
    collection = get_or_create_collection(repo_id)
    [query_embedding] = embed_texts([query])

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for doc, meta in zip(documents, metadatas):
        chunks.append(
            RetrievedChunk(
                content=doc or "",
                file_path=str(meta.get("filePath", "unknown")),
                start_line=int(meta.get("startLine", 0)),
                end_line=int(meta.get("endLine", 0)),
                symbol_name=str(meta["symbolName"]) if meta.get("symbolName") else None,
            )
        )
    return chunks
