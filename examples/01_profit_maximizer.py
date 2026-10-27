"""Example 1 — Minimal profit-maximizer loop.

Runs 10 decision cycles. Each cycle the LLM checks state and optionally
buys a field if conditions are met.

Run:

    export COSMERGON_PLAYER_TOKEN="CSMR-..."
    export OPENAI_API_KEY="sk-..."
    pip install langchain-cosmergon langchain-openai
    python 01_profit_maximizer.py
"""

from __future__ import annotations

import os
import time
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from langchain_cosmergon import cosmergon_tools

MAX_TOOL_ROUNDS = 5


def run_with_tools(llm: Any, tools: list[Any], prompt: str) -> str:
    """Ask the tool-bound model and execute the tool calls it requests.

    ``bind_tools(...).invoke(...)`` only returns the requested calls; something has to run
    them and hand the results back as ``ToolMessage``. At most ``MAX_TOOL_ROUNDS`` rounds.
    """
    by_name = {t.name: t for t in tools}
    messages: list[Any] = [HumanMessage(content=prompt)]
    reply = llm.invoke(messages)
    for _ in range(MAX_TOOL_ROUNDS):
        if not reply.tool_calls:
            break
        messages.append(reply)
        for call in reply.tool_calls:
            result = by_name[call["name"]].invoke(call["args"])
            messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
        reply = llm.invoke(messages)
    return str(reply.content)


def main() -> None:
    tools = cosmergon_tools(
        player_token=os.environ["COSMERGON_PLAYER_TOKEN"],
        agent_name=os.environ.get("COSMERGON_AGENT_NAME"),  # optional
    )

    llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)

    for cycle in range(10):
        print(f"\n=== Cycle {cycle + 1}/10 ===")
        answer = run_with_tools(
            llm,
            tools,
            "Check your current Cosmergon state (observe). "
            "If your energy balance is above 2000 and you own fewer than 5 fields, "
            "buy the cheapest available field (act). Otherwise wait. "
            "Be concise in your response.",
        )
        print(answer)

        # Respect Cosmergon tick interval (60s)
        time.sleep(60)


if __name__ == "__main__":
    main()
