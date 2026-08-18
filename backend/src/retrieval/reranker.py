import os
import re


def normalize_name(name: str) -> str:
    """
    Normalize filenames/symbols for comparison.

    Example:
        Navbar.jsx -> navbar
        navbar.js  -> navbar
        Navbar     -> navbar
    """
    name = name.lower().strip()

    # Remove extension
    name = os.path.splitext(name)[0]

    # Remove non-alphanumeric characters
    name = re.sub(r"[^a-z0-9]", "", name)

    return name


def rerank_results(query: str, results: list) -> list:
    query_lower = query.lower()

    # Extract words from query
    query_words = re.findall(
        r"[a-zA-Z0-9_.-]+",
        query_lower,
    )

    # Normalize query words
    normalized_query_words = {
        normalize_name(word)
        for word in query_words
        if normalize_name(word)
    }

    for result in results:

        file_path = result["filePath"]
        symbol_name = result.get("symbolName") or ""

        filename = os.path.basename(file_path)

        normalized_filename = normalize_name(filename)
        normalized_symbol = normalize_name(symbol_name)

        score = result.get("score", 0)

        # --------------------------------
        # Filename match
        # --------------------------------

        if normalized_filename in normalized_query_words:
            score += 2.0

        # --------------------------------
        # Symbol match
        # --------------------------------

        if normalized_symbol in normalized_query_words:
            score += 2.0

        # --------------------------------
        # Filename appears in query
        # --------------------------------

        for word in normalized_query_words:

            if not word:
                continue

            if word == normalized_filename:
                score += 1.0

            elif word in normalized_filename:
                score += 0.5

        result["final_score"] = score

    return sorted(
        results,
        key=lambda x: x["final_score"],
        reverse=True,
    )