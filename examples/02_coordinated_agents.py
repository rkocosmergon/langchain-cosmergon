"""Example 2 — Two coordinated agents (scout + trader).

Uses a single master-key (player_token) to control two named agents.
Scout reports market opportunities, trader acts on them.

Run:

    export COSMERGON_PLAYER_TOKEN="CSMR-..."
    export OPENAI_API_KEY="sk-..."
    pip install langchain-cosmergon langchain-openai
    python 02_coordinated_agents.py
"""

from __future__ import annotations

import os
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
    token = os.environ["COSMERGON_PLAYER_TOKEN"]

    # Two agents under the same master-key — each gets its own tool set
    scout_tools = cosmergon_tools(player_token=token, agent_name="scout")
    trader_tools = cosmergon_tools(player_token=token, agent_name="trader")

    llm = ChatOpenAI(model="gpt-4o-mini")
    scout = llm.bind_tools(scout_tools)
    trader = llm.bind_tools(trader_tools)

    # Step 1: Scout reports opportunities
    scout_report = run_with_tools(
        scout,
        scout_tools,
        "Use the observe tool with detail='rich' to check the current market. "
        "Identify up to 3 arbitrage opportunities (items priced below recent median). "
        "Return a structured summary.",
    )
    print("--- SCOUT REPORT ---")
    print(scout_report)

    # Step 2: Trader acts on the best opportunity
    trader_decision = run_with_tools(
        trader,
        trader_tools,
        f"Scout report: {scout_report}\n"
        "Pick the single best arbitrage and execute it via act(). "
        "If no opportunity meets your quality threshold, explain why and do nothing.",
    )
    print("\n--- TRADER DECISION ---")
    print(trader_decision)


if __name__ == "__main__":
    main()
