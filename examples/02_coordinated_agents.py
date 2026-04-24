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

from langchain_openai import ChatOpenAI

from langchain_cosmergon import cosmergon_tools


def main() -> None:
    token = os.environ["COSMERGON_PLAYER_TOKEN"]

    # Two agents under the same master-key — each gets its own tool set
    scout_tools = cosmergon_tools(player_token=token, agent_name="scout")
    trader_tools = cosmergon_tools(player_token=token, agent_name="trader")

    llm = ChatOpenAI(model="gpt-4o-mini")
    scout = llm.bind_tools(scout_tools)
    trader = llm.bind_tools(trader_tools)

    # Step 1: Scout reports opportunities
    scout_report = scout.invoke(
        "Use the observe tool with detail='rich' to check the current market. "
        "Identify up to 3 arbitrage opportunities (items priced below recent median). "
        "Return a structured summary."
    )
    print("--- SCOUT REPORT ---")
    print(scout_report.content if hasattr(scout_report, "content") else scout_report)

    # Step 2: Trader acts on the best opportunity
    report_text = scout_report.content if hasattr(scout_report, "content") else scout_report
    trader_decision = trader.invoke(
        f"Scout report: {report_text}\n"
        "Pick the single best arbitrage and execute it via act(). "
        "If no opportunity meets your quality threshold, explain why and do nothing."
    )
    print("\n--- TRADER DECISION ---")
    print(trader_decision.content if hasattr(trader_decision, "content") else trader_decision)


if __name__ == "__main__":
    main()
