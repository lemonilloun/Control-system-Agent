from typing import Any, List, TypedDict

from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    messages: List[BaseMessage]
    theory: str | None
    citations: list[dict]
    iterations: int
    output: Any | None
