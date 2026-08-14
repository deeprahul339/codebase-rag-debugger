"""
Exact/substring symbol lookup — useful as a complement to vector search
for questions like "where is `handle_auth` defined", where embedding
similarity alone can miss an exact identifier match.
"""

from ..ingestion.indexer import get_or_create_collection


def find_by_symbol_name(repo_id: str, symbol_name: str) -> list[dict]:
    collection = get_or_create_collection(repo_id)

    results = collection.get(where={"symbolName": symbol_name})

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    return [
        {"content": doc, "metadata": meta}
        for doc, meta in zip(documents, metadatas)
    ]
