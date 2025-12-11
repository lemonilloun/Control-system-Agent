import ast
import json
import hashlib
from typing import Any, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph

from app.agents.state import AgentState
from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import TOOLS
from app.clients.ollama_client import get_llm
from app.clients.redis_client import get_redis

_executor: Runnable | None = None
CACHE_TTL_SECONDS = 24 * 60 * 60


async def call_llm_with_tools(state: AgentState) -> AgentState:
    llm = get_llm().bind_tools(TOOLS)
    messages = state["messages"]
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    # Log incoming turn
    if messages:
        last_user = [m for m in messages if isinstance(m, HumanMessage)][-1]
        import logging
        logging.getLogger(__name__).info(f"[graph] LLM step, last user: {last_user.content}")
    result = await llm.ainvoke([system_msg] + messages)
    tool_calls = getattr(result, "tool_calls", None) or []
    logging.getLogger(__name__).info(f"[graph] LLM responded, tool_calls={ [tc.get('name') for tc in tool_calls] if tool_calls else []}")
    state["messages"] = messages + [result]
    return state


async def execute_tools(state: AgentState) -> AgentState:
    messages = state["messages"]
    last = messages[-1]

    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return state

    tool_map = {t.name: t for t in TOOLS}
    import logging

    for tc in tool_calls:
        name = tc.get("name")
        args = tc.get("args") or tc.get("arguments") or {}
        call_id = tc.get("id", name)

        tool = tool_map.get(name)
        if tool is None:
            messages.append(
                ToolMessage(
                    content=f"Unknown tool {name}",
                    tool_call_id=call_id,
                    name=name or "unknown_tool",
                )
            )
            continue

        logging.getLogger(__name__).info(f"[graph] invoking tool {name} args={args}")
        result = await tool.ainvoke(args)
        logging.getLogger(__name__).info(f"[graph] tool {name} done")

        messages.append(
            ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=call_id,
                name=name,
            )
        )

    state["messages"] = messages
    state["iterations"] = state.get("iterations", 0) + 1
    return state


def should_continue(state: AgentState) -> str:
    messages = state["messages"]
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []
    if tool_calls:
        return "tools"
    if state.get("iterations", 0) > 3:
        return "end"
    return "end"


def build_graph() -> Runnable:
    graph = StateGraph(AgentState)

    graph.add_node("agent", call_llm_with_tools)
    graph.add_node("tools", execute_tools)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")

    return graph.compile()


def get_agent_executor() -> Runnable:
    global _executor
    if _executor is None:
        _executor = build_graph()
    return _executor


def _safe_parse(content: Any) -> Any:
    if isinstance(content, (dict, list)):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except Exception:
            try:
                return ast.literal_eval(content)
            except Exception:
                return content
    return content


async def run_agent(question: str) -> Dict[str, Any]:
    cache_key = f"llm_cache:{hashlib.sha1(question.encode('utf-8')).hexdigest()}"
    redis_client = None
    try:
        redis_client = get_redis()
    except Exception:
        redis_client = None

    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                import logging
                logging.getLogger(__name__).info(f"[cache] hit for question")
                return data
            except Exception:
                pass

    executor = get_agent_executor()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "theory": None,
        "citations": [],
        "iterations": 0,
        "output": None,
    }
    result_state = await executor.ainvoke(initial_state)
    ai_messages = [m for m in result_state["messages"] if isinstance(m, AIMessage)]
    answer = ai_messages[-1].content if ai_messages else ""

    citations: List[Dict[str, Any]] = []
    for m in reversed(result_state["messages"]):
        if isinstance(m, ToolMessage):
            parsed = _safe_parse(m.content)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        citations.append(
                            {
                                "chunk_id": item.get("chunk_id"),
                                "book_id": item.get("book_id"),
                                "theory": item.get("theory"),
                                "pages": [item.get("page_start"), item.get("page_end")],
                                "score": item.get("score"),
                            }
                        )
            break

    return {
        "answer": answer,
        "citations": citations,
        "theory": result_state.get("theory"),
    }

    result = {
        "answer": answer,
        "citations": citations,
        "theory": result_state.get("theory"),
    }

    if redis_client:
        try:
            redis_client.set(cache_key, json.dumps(result, ensure_ascii=False), ex=CACHE_TTL_SECONDS)
            import logging
            logging.getLogger(__name__).info(f"[cache] stored result for question")
        except Exception:
            pass

    return result
