from dataclasses import dataclass, field


@dataclass
class AgentState:
    repo_id: str
    user_question: str

    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)

    final_answer: str | None = None