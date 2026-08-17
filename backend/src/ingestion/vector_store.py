import json
import os
import threading
from typing import Any

import faiss
import numpy as np


class FAISSVectorStore:
    """
    Local persistent FAISS vector store.

    Each repository gets:
        <collection_name>.index
        <collection_name>.json

    The .index file stores vectors.
    The .json file stores the metadata/content corresponding
    to each vector.
    """

    def __init__(
        self,
        index_dir: str,
        collection_name: str,
    ):
        self.index_dir = index_dir
        self.collection_name = collection_name

        os.makedirs(
            self.index_dir,
            exist_ok=True,
        )

        self.index_path = os.path.join(
            self.index_dir,
            f"{self.collection_name}.index",
        )

        self.metadata_path = os.path.join(
            self.index_dir,
            f"{self.collection_name}.json",
        )

        self.index = None
        self.metadata: list[dict[str, Any]] = []

        self._lock = threading.Lock()

        self._load()

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _load(self):
        """
        Load the FAISS index and metadata from disk if they exist.
        """

        if os.path.exists(self.index_path):
        
            self.index = faiss.read_index(
                self.index_path
            )

        if os.path.exists(self.metadata_path):
            with open(
                self.metadata_path,
                "r",
                encoding="utf-8",
            ) as f:
                self.metadata = json.load(f)

            

        # Make sure the vector count and metadata count match.
        if self.index is not None:

            if self.index.ntotal != len(
                self.metadata
            ):
                raise ValueError(
                    "FAISS index and metadata are out of sync: "
                    f"{self.index.ntotal} vectors but "
                    f"{len(self.metadata)} metadata entries."
                )

    # ------------------------------------------------------------------
    # Add vectors
    # ------------------------------------------------------------------

    def add(
        self,
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
    ):
        """
        Add embeddings and their corresponding metadata.
        """

        if not embeddings:
            return

        if len(embeddings) != len(metadata):
            raise ValueError(
                "Embeddings and metadata must have the same length. "
                f"Got {len(embeddings)} embeddings and "
                f"{len(metadata)} metadata entries."
            )

        vectors = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if vectors.ndim != 2:
            raise ValueError(
                "Embeddings must be a 2D array."
            )

        dimension = vectors.shape[1]

        with self._lock:

            # Create the FAISS index on the first insert.
            if self.index is None:

                self.index = faiss.IndexFlatL2(
                    dimension
                )

            else:

                # Make sure future embeddings have
                # the same dimension.
                if self.index.d != dimension:
                    raise ValueError(
                        "Embedding dimension does not match "
                        "the existing FAISS index. "
                        f"Expected {self.index.d}, "
                        f"got {dimension}."
                    )

            self.index.add(
                vectors
            )

            self.metadata.extend(
                metadata
            )

            self._save()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save(self):
        """
        Persist FAISS index and metadata to disk.
        """

        if self.index is None:
            return

        faiss.write_index(
            self.index,
            self.index_path,
        )

        with open(
            self.metadata_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.metadata,
                f,
                ensure_ascii=False,
                indent=2,
            )


    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def count(self) -> int:
        """
        Return the number of vectors stored in FAISS.
        """

        if self.index is None:
            return 0

        return self.index.ntotal

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        embedding: list[float],
        k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search for the k most similar vectors.

        Returns:

        [
            {
                "distance": 123.45,
                "metadata": {...}
            }
        ]
        """

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        if not embedding:
            return []

        query = np.asarray(
            [embedding],
            dtype=np.float32,
        )

        # Make sure the query dimension matches
        # the FAISS index dimension.
        if query.shape[1] != self.index.d:
            raise ValueError(
                "Query embedding dimension does not match "
                "the FAISS index dimension. "
                f"Expected {self.index.d}, "
                f"got {query.shape[1]}."
            )

        k = min(
            k,
            self.index.ntotal,
        )

        distances, indices = self.index.search(
            query,
            k,
        )

        results: list[dict[str, Any]] = []

        for distance, index in zip(
            distances[0],
            indices[0],
        ):

            if index < 0:
                continue

            if index >= len(
                self.metadata
            ):
                continue

            results.append(
                {
                    "distance": float(
                        distance
                    ),
                    "metadata": self.metadata[
                        index
                    ],
                }
            )

        return results