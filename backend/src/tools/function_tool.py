from pathlib import Path

from .function_extractors.python import extract_python_function
from .function_extractors.javascript import extract_javascript_function
from .function_extractors.typescript import extract_typescript_function


WORKSPACE_DIR = Path(".workspace")


def get_function(
    repo_id: str,
    file_path: str,
    function_name: str,
) -> dict:

    if not repo_id:
        raise ValueError("Repository ID is required.")

    if not file_path:
        raise ValueError("File path is required.")

    if not function_name:
        raise ValueError("Function name is required.")

    repo_root = (WORKSPACE_DIR / repo_id).resolve()
    target_file = (repo_root / file_path).resolve()

    # Security check
    try:
        target_file.relative_to(repo_root)
    except ValueError:
        raise ValueError(
            "File path is outside the repository."
        )

    if not target_file.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    if not target_file.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    extension = target_file.suffix.lower()

    source = target_file.read_text(
        encoding="utf-8",
        errors="replace",
    )

    # -----------------------------------------
    # Select language extractor
    # -----------------------------------------

    if extension == ".py":

        result = extract_python_function(
            source,
            function_name,
        )

    elif extension in {".js", ".jsx"}:

        result = extract_javascript_function(
            source,
            function_name,
        )

    elif extension in {".ts", ".tsx"}:

        result = extract_typescript_function(
            source,
            function_name,
        )

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    if result is None:
        raise ValueError(
            f"Function '{function_name}' "
            f"not found in {file_path}"
        )

    start_line, end_line, content = result

    return {
        "filePath": file_path,
        "functionName": function_name,
        "startLine": start_line,
        "endLine": end_line,
        "content": content,
    }