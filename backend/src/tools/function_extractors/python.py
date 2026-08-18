import ast


def extract_python_function(
    source: str,
    function_name: str,
):
    """
    Extract a Python function using AST.
    """

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    lines = source.splitlines()

    for node in ast.walk(tree):

        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):

            if node.name != function_name:
                continue

            start_line = node.lineno
            end_line = node.end_lineno

            content = "\n".join(
                lines[start_line - 1:end_line]
            )

            return (
                start_line,
                end_line,
                content,
            )

    return None