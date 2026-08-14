"""
THE DIFFERENTIATOR: chunk by function/class boundary, not fixed-size
text windows. This is what separates a serious code-RAG tool from a
"paste your repo into a text splitter" demo.

v1 approach: regex-based boundary detection per language (fast to ship
in 2-3 days). Swap in `tree-sitter` + `tree-sitter-languages` for real
AST parsing once the pipeline works end-to-end — the ScannedFile ->
list[CodeChunk] interface below is designed so that swap doesn't touch
any other file.

TODO (post-hackathon polish): replace `chunk_file` internals with
tree-sitter queries per language for accurate function/class nodes.
"""

import re
from dataclasses import dataclass, field

from .file_scanner import ScannedFile

LANGUAGE_BY_EXT = {
    ".ts": "typescript", ".tsx": "tsx",
    ".js": "javascript", ".jsx": "jsx",
    ".py": "python", ".go": "go", ".rs": "rust",
    ".java": "java", ".rb": "ruby", ".php": "php",
    ".c": "c", ".cpp": "cpp", ".h": "c",
}

# Rough boundary markers per language family — good enough for v1.
BOUNDARY_PATTERNS = {
    "typescript": re.compile(
        r"^\s*(?:export\s+)?(?:default\s+)?"
        r"(?:(?:async\s+)?function|class|interface|type)\s+"
        r"([A-Za-z0-9_]+)"
        r"|"
        r"^\s*(?:export\s+)?(?:async\s+)?"
        r"(?:const|let|var)\s+([A-Za-z0-9_]+)\s*="
    ),

    "tsx": re.compile(
        r"^\s*(?:export\s+)?(?:default\s+)?"
        r"(?:(?:async\s+)?function|class|interface|type)\s+"
        r"([A-Za-z0-9_]+)"
        r"|"
        r"^\s*(?:export\s+)?(?:async\s+)?"
        r"(?:const|let|var)\s+([A-Za-z0-9_]+)\s*="
    ),

    "javascript": re.compile(
        r"^\s*(?:export\s+)?(?:default\s+)?"
        r"(?:(?:async\s+)?function|class)\s+"
        r"([A-Za-z0-9_]+)"
        r"|"
        r"^\s*(?:export\s+)?(?:async\s+)?"
        r"(?:const|let|var)\s+([A-Za-z0-9_]+)\s*="
    ),

    "jsx": re.compile(
        r"^\s*(?:export\s+)?(?:default\s+)?"
        r"(?:(?:async\s+)?function|class)\s+"
        r"([A-Za-z0-9_]+)"
        r"|"
        r"^\s*(?:export\s+)?(?:async\s+)?"
        r"(?:const|let|var)\s+([A-Za-z0-9_]+)\s*="
    ),

    "python": re.compile(
        r"^\s*(?:def|class)\s+([A-Za-z0-9_]+)"
    ),

    "go": re.compile(
        r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z0-9_]+)"
    ),

    "default": re.compile(
        r"^\s*(?:function|class|def|func)\s+([A-Za-z0-9_]+)"
    ),
}


@dataclass
class CodeChunk:
    id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    language: str
    symbol_name: str | None = None
    symbol_type: str = "block"  # "function" | "class" | "method" | "block"


def _pattern_for(language: str) -> re.Pattern:
    return BOUNDARY_PATTERNS.get(language, BOUNDARY_PATTERNS["default"])


def chunk_file(file: ScannedFile) -> list[CodeChunk]:
    language = LANGUAGE_BY_EXT.get(file.extension, "text")

    with open(file.absolute_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    lines = source.split("\n")
    pattern = _pattern_for(language)

    boundaries: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            name = next(group for group in match.groups() if group is not None)
            boundaries.append((idx, name))

    # No detected symbols (config file, small script) — treat as one chunk.
    if not boundaries:
        return [
            CodeChunk(
                id=f"{file.relative_path}:0",
                file_path=file.relative_path,
                start_line=1,
                end_line=len(lines),
                content=source,
                language=language,
                symbol_type="block",
            )
        ]

    chunks: list[CodeChunk] = []
    for i, (start, name) in enumerate(boundaries):
        end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(lines)
        content = "\n".join(lines[start:end]).strip()
        if not content:
            continue

        chunks.append(
            CodeChunk(
                id=f"{file.relative_path}:{start}",
                file_path=file.relative_path,
                start_line=start + 1,
                end_line=end,
                content=content,
                symbol_name=name,
                symbol_type="function",
                language=language,
            )
        )

    return chunks


def chunk_repository(files: list[ScannedFile]) -> list[CodeChunk]:
    all_chunks: list[CodeChunk] = []
    for file in files:
        all_chunks.extend(chunk_file(file))
    return all_chunks
