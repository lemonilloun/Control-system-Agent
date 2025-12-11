import logging
from fastapi import APIRouter

from app.schemas.agent import AgentAnswer, AgentQuery
from app.agents.graph import run_agent

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/ask", response_model=AgentAnswer)
async def ask_agent(payload: AgentQuery) -> AgentAnswer:
    log.info(f"[api] received question: {payload.question}")
    result = await run_agent(payload.question)
    log.info(f"[api] finished question, answer_len={len(result.get('answer',''))}, citations={len(result.get('citations',[]))}")
    return AgentAnswer(**result)
