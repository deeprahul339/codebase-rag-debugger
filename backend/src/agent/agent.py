import os

from google import genai

from google.genai import types
from dotenv import load_dotenv
from .state import AgentState
from .prompts import SYSTEM_PROMPT

from src.tools.file_tool import get_file
from src.tools.find_references_tool import find_references
from src.tools.function_tool import get_function
from src.tools.search_code import search_code

from .events import (
    tool_start_event,
    tool_result_event,
    final_event,
    error_event,
)
load_dotenv()

TOOLS = {
    "search_code": search_code,
    "get_file": get_file,
    "get_function": get_function,
    "find_references": find_references,
}


GEMINI_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "search_code",
                "description": "Search the repository for relevant code.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "repo_id": {
                            "type": "STRING",
                            "description": "Repository ID.",
                        },
                        "query": {
                            "type": "STRING",
                            "description": "Search query.",
                        },
                    },
                    "required": ["repo_id", "query"],
                },
            },
            {
                "name": "get_file",
                "description": "Read a file from the repository.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "repo_id": {
                            "type": "STRING",
                            "description": "Repository ID.",
                        },
                        "file_path": {
                            "type": "STRING",
                            "description": "Repository file path.",
                        },
                    },
                    "required": ["repo_id", "file_path"],
                },
            },
            {
                "name": "get_function",
                "description": "Extract a function from a source file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "repo_id": {
                            "type": "STRING",
                            "description": "Repository ID.",
                        },
                        "file_path": {
                            "type": "STRING",
                            "description": "Repository file path.",
                        },
                        "function_name": {
                            "type": "STRING",
                            "description": "Function name.",
                        },
                    },
                    "required": [
                        "repo_id",
                        "file_path",
                        "function_name",
                    ],
                },
            },
            {
                "name": "find_references",
                "description": "Find references to a symbol in the repository.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "repo_id": {
                            "type": "STRING",
                            "description": "Repository ID.",
                        },
                        "symbol_name": {
                            "type": "STRING",
                            "description": "Symbol name.",
                        },
                    },
                    "required": [
                        "repo_id",
                        "symbol_name",
                    ],
                },
            },
        ]
    }
]


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_tool_result_message(
    tool_name: str,
    tool_args: dict,
    tool_result,
) -> str:

    if isinstance(tool_result, dict) and "error" in tool_result:
        return f"Error: {tool_result['error']}"

    if tool_name == "search_code":
        if isinstance(tool_result, list):
            return f"{len(tool_result)} relevant results found"
        return "Code search completed"

    if tool_name == "get_file":
        return "File inspected"

    if tool_name == "get_function":
        function_name = tool_args.get(
            "function_name",
            "function",
        )
        return f"Inspected {function_name}()"

    if tool_name == "find_references":
        if isinstance(tool_result, list):
            return f"{len(tool_result)} references found"
        return "References found"

    return "Tool completed"

def run_agent(
    repo_id: str,
    user_question: str,
):
    state = AgentState(
        repo_id=repo_id,
        user_question=user_question,
    )

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(
                    text=f"""
Repository ID:
{repo_id}

User question:
{user_question}
"""
                )
            ],
        )
    ]

    while True:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=GEMINI_TOOLS,
            ),
        )

        function_calls = [
            part.function_call
            for part in response.candidates[0].content.parts
            if part.function_call
        ]

        # --------------------------------
        # GEMINI HAS FINISHED
        # --------------------------------

        if not function_calls:
            state.final_answer = response.text

            # Send final answer event
            yield final_event(response.text)

            return

        # --------------------------------
        # SAVE GEMINI'S FUNCTION CALL
        # --------------------------------

        contents.append(response.candidates[0].content)

        tool_response_parts = []

        # --------------------------------
        # EXECUTE TOOLS
        # --------------------------------

        for function_call in function_calls:

            tool_name = function_call.name
            tool_args = dict(function_call.args)

            # Save tool call in state
            state.tool_calls.append(
                {
                    "tool": tool_name,
                    "arguments": tool_args,
                }
            )

            # --------------------------------
            # FIND TOOL
            # --------------------------------

            tool = TOOLS.get(tool_name)

            if tool is None:
                yield error_event(
                    f"Unknown tool requested: {tool_name}"
                )
                return

            # --------------------------------
            # TOOL START EVENT
            # --------------------------------

            yield tool_start_event(
                tool_name,
                tool_args,
            )

            # --------------------------------
            # EXECUTE PYTHON TOOL
            # --------------------------------

            try:
                tool_result = tool(**tool_args)

            except Exception as e:
                tool_result = {
                    "error": str(e)
                }

            # --------------------------------
            # SAVE TOOL RESULT
            # --------------------------------

            state.tool_results.append(
                {
                    "tool": tool_name,
                    "result": tool_result,
                }
            )

            # --------------------------------
            # CREATE HUMAN-READABLE RESULT
            # --------------------------------

            message = get_tool_result_message(
                tool_name,
    tool_args,
    tool_result,
            )

            # --------------------------------
            # TOOL RESULT EVENT
            # --------------------------------

            yield tool_result_event(
                tool_name,
                message,
            )

            # --------------------------------
            # BUILD GEMINI FUNCTION RESPONSE
            # --------------------------------

            tool_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response={
                        "result": tool_result,
                    },
                   
                )
            )

        # --------------------------------
        # SEND TOOL RESULTS BACK TO GEMINI
        # --------------------------------

        contents.append(
            types.Content(
                role="user",
                parts=tool_response_parts,
            )
        )