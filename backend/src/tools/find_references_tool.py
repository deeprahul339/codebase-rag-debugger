from pathlib import Path
import re


WORKSPACE_DIR = Path(".workspace")

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}


def find_references(
    repo_id: str,
    symbol_name: str,
) -> dict:
    """
    Find references/usages of a function, class, or symbol
    throughout a repository.

    Args:
        repo_id: Repository ID.
        symbol_name: Function/class/variable name.

    Returns:
        Dictionary containing all matching references.
    """

    if not repo_id:
        raise ValueError("Repository ID is required.")

    if not symbol_name:
        raise ValueError("Symbol name is required.")

    # ---------------------------------------------------------
    # Repository root
    # ---------------------------------------------------------

    repo_root = (WORKSPACE_DIR / repo_id).resolve()

    if not repo_root.exists():
        raise FileNotFoundError(
            f"Repository not found: {repo_id}"
        )

    if not repo_root.is_dir():
        raise ValueError(
            f"Repository path is not a directory: {repo_id}"
        )

    # ---------------------------------------------------------
    # Create symbol pattern
    #
    # \b prevents matching:
    #
    # index_repository
    #
    # inside:
    #
    # my_index_repository_test
    # ---------------------------------------------------------

    pattern = re.compile(
        rf"\b{re.escape(symbol_name)}\b"
    )

    references = []

    # ---------------------------------------------------------
    # Walk repository
    # ---------------------------------------------------------

    for file_path in repo_root.rglob("*"):

        if not file_path.is_file():
            continue

        # Only supported source files
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # Skip common directories
        if any(
            part in {
                "node_modules",
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                "dist",
                "build",
            }
            for part in file_path.parts
        ):
            continue

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except Exception:
            continue

        lines = content.splitlines()

        # -----------------------------------------------------
        # Search every line
        # -----------------------------------------------------

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            if not pattern.search(line):
                continue

            relative_path = file_path.relative_to(
                repo_root
            )

            references.append(
                {
                    "filePath": relative_path.as_posix(),
                    "line": line_number,
                    "content": line.strip(),
                }
            )

    return {
        "symbolName": symbol_name,
        "referenceCount": len(references),
        "references": references,
    }