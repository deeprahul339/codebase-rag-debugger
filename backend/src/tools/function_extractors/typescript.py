from .javascript import extract_javascript_function


def extract_typescript_function(
    source: str,
    function_name: str,
):
    """
    Extract TypeScript / TSX functions.

    Uses the JavaScript extractor for the
    common function forms.
    """

    return extract_javascript_function(
        source,
        function_name,
    )