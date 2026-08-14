"""
Walks a cloned repo directory and returns a list of source files worth
indexing. Keep this simple in v1: extension allow-list + ignore-list.
TODO: respect .gitignore properly (e.g. via the `pathspec` package).
"""

import os
from dataclasses import dataclass

ALLOWED_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx",
    ".py", ".go", ".rs", ".java",
    ".rb", ".php", ".c", ".cpp", ".h",
}

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", "out",
    "venv", ".venv", "__pycache__", ".next", "coverage",
}

MAX_FILE_SIZE_BYTES = 500_000


@dataclass
class ScannedFile:
    absolute_path: str
    relative_path: str
    extension: str
    size_bytes: int


def scan_repository(root_dir: str) -> list[ScannedFile]:
    results: list[ScannedFile] = []

    for current_dir, dirnames, filenames in os.walk(root_dir):
        # prune ignored/hidden directories in place so os.walk skips them
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext not in ALLOWED_EXTENSIONS:
                continue

            absolute_path = os.path.join(current_dir, filename)
            try:
                size_bytes = os.path.getsize(absolute_path)
            except OSError:
                continue

            if size_bytes > MAX_FILE_SIZE_BYTES:
                continue

            results.append(
                ScannedFile(
                    absolute_path=absolute_path,
                    relative_path=os.path.relpath(absolute_path, root_dir),
                    extension=ext,
                    size_bytes=size_bytes,
                )
            )

    return results
