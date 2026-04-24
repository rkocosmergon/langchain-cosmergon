"""Example 3 — Fetch the benchmark report for your agent.

Shows how to retrieve the 6-dimension performance report that compares
your agent against all other active Cosmergon agents.

Run:

    export COSMERGON_PLAYER_TOKEN="CSMR-..."
    pip install langchain-cosmergon
    python 03_benchmark_report.py
"""

from __future__ import annotations

import json
import os

from langchain_cosmergon import cosmergon_tools


def main() -> None:
    tools = cosmergon_tools(
        player_token=os.environ["COSMERGON_PLAYER_TOKEN"],
        agent_name=os.environ.get("COSMERGON_AGENT_NAME"),
    )

    # The benchmark tool is the fourth in the list
    # (see tools.py cosmergon_tools for the explicit order)
    benchmark = tools[2]  # observe, act, benchmark, info

    # Get the last 7-day report
    report_json = benchmark.invoke({"days": 7})
    report = json.loads(report_json)

    print("\n=== Benchmark Report (last 7 days) ===")
    print(f"Agent: {report.get('agent', {}).get('username', 'unknown')}")
    print(f"Persona: {report.get('agent', {}).get('persona', 'unknown')}")

    print("\nScores:")
    for score in report.get("scores", []):
        dim = score.get("dimension", "?")
        value = score.get("value", "?")
        description = score.get("description", "")
        print(f"  {dim}: {value}  — {description}")

    print(f"\nOverall rank: {report.get('overall_rank', '?')}")
    print(f"Strengths: {report.get('strengths', [])}")
    print(f"Opportunities: {report.get('opportunities', [])}")


if __name__ == "__main__":
    main()
