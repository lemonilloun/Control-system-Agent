from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentQuery(BaseModel):
    question: str = Field(..., description="Вопрос по теории управления")
    chat_history: Optional[List[Dict[str, Any]]] = None


class AgentAnswer(BaseModel):
    answer: str
    citations: List[Dict[str, Any]] = []
    theory: str | None = None
