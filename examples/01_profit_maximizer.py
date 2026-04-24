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

from langchain_openai import ChatOpenAI

from langchain_cosmergon import cosmergon_tools


def main() -> None:
    tools = cosmergon_tools(
        player_token=os.environ["COSMERGON_PLAYER_TOKEN"],
        agent_name=os.environ.get("COSMERGON_AGENT_NAME"),  # optional
    )

    llm = ChatOpenAI(model="gpt-4o-mini").bind_tools(tools)

    for cycle in range(10):
        print(f"\n=== Cycle {cycle + 1}/10 ===")
        response = llm.invoke(
            "Check your current Cosmergon state (observe). "
            "If your energy balance is above 2000 and you own fewer than 5 fields, "
            "buy the cheapest available field (act). Otherwise wait. "
            "Be concise in your response."
        )
        print(response.content if hasattr(response, "content") else response)

        # Respect Cosmergon tick interval (60s)
        time.sleep(60)


if __name__ == "__main__":
    main()
