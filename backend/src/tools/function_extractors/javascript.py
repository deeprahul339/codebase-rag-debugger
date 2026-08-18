import re


def extract_javascript_function(
    source: str,
    function_name: str,
):
    """
    Extract JavaScript / JSX functions.

    Supports common forms:

        function foo() {}

        async function foo() {}

        export function foo() {}

        const foo = () => {}

        const foo = function () {}

        export const foo = () => {}
    """

    lines = source.splitlines()

    patterns = [

        # function foo()
        re.compile(
            rf"^\s*"
            rf"(?:export\s+)?"
            rf"(?:default\s+)?"
            rf"(?:async\s+)?"
            rf"function\s+"
            rf"{re.escape(function_name)}\s*\("
        ),

        # const foo = ...
        re.compile(
            rf"^\s*"
            rf"(?:export\s+)?"
            rf"(?:const|let|var)\s+"
            rf"{re.escape(function_name)}\s*="
        ),

        # class method
        re.compile(
            rf"^\s*"
            rf"(?:async\s+)?"
            rf"{re.escape(function_name)}\s*\("
        ),
    ]

    start_index = None

    for i, line in enumerate(lines):

        for pattern in patterns:

            if pattern.search(line):
                start_index = i
                break

        if start_index is not None:
            break

    if start_index is None:
        return None

    return extract_braced_block(
        lines,
        start_index,
    )


def extract_braced_block(
    lines: list[str],
    start_index: int,
):

    brace_count = 0
    found_brace = False

    for i in range(
        start_index,
        len(lines),
    ):

        line = remove_comments_and_strings(
            lines[i]
        )

        for char in line:

            if char == "{":
                brace_count += 1
                found_brace = True

            elif char == "}":
                brace_count -= 1

        if found_brace and brace_count == 0:

            start_line = start_index + 1
            end_line = i + 1

            content = "\n".join(
                lines[start_index:i + 1]
            )

            return (
                start_line,
                end_line,
                content,
            )

    return None


def remove_comments_and_strings(
    line: str,
):

    line = re.sub(
        r"//.*",
        "",
        line,
    )

    line = re.sub(
        r'(["\']).*?\1',
        "",
        line,
    )

    return line