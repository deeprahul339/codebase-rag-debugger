def tool_start_event(tool_name: str, arguments: dict):
    return {
        "type": "TOOL_START",
        "tool": tool_name,
        "arguments": arguments,
    }


def tool_result_event(tool_name: str, message: str):
    return {
        "type": "TOOL_RESULT",
        "tool": tool_name,
        "message": message,
    }


def final_event(answer: str):
    return {
        "type": "FINAL",
        "answer": answer,
    }


def error_event(message: str):
    return {
        "type": "ERROR",
        "message": message,
    }