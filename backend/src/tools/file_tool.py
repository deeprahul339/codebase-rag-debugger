from pathlib import Path


WORKSPACE_DIR = Path(".workspace")


def get_file(repo_id: str, file_path: str) -> dict:
    """
    Read a file from an indexed repository.

    Args:
        repo_id: Repository ID.
        file_path: Path relative to the repository root.

    Returns:
        File information and contents.
    """

    if not repo_id:
        raise ValueError("Repository ID is required.")

    if not file_path:
        raise ValueError("File path is required.")

    # Repository root
    repo_root = (WORKSPACE_DIR / repo_id).resolve()

    # Requested file
    target_file = (repo_root / file_path).resolve()

    # Security check:
    # Prevent paths such as ../../.env
    try:
        target_file.relative_to(repo_root)
    except ValueError:
        raise ValueError("File path is outside the repository.")

    # Check that file exists
    if not target_file.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    # Make sure it is actually a file
    if not target_file.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    try:
        content = target_file.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:
        raise RuntimeError(
            f"Unable to read file: {e}"
        )

    return {
        "filePath": file_path,
        "content": content,
        "lineCount": len(content.splitlines()),
    }