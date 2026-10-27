"""Example 4 — Local LLM via Ollama (no cloud API key required).

Demonstrates that Cosmergon is truly model-agnostic: the exact same code
works with a local Ollama LLM (llama3.2, qwen3, gemma3, ...). Privacy-
conscious users or those without OpenAI/Anthropic accounts can still
run Cosmergon agents.

Prerequisites:

    # 1. Install Ollama locally: https://ollama.com/download
    # 2. Pull a tool-capable model:
    ollama pull llama3.2:3b

    pip install langchain-cosmergon langchain-ollama
    export COSMERGON_PLAYER_TOKEN="CSMR-..."
    python 04_local_ollama.py

Note on tool-calling: not every Ollama model supports function-calling
reliably. llama3.2:3b and qwen2.5:7b are known to work well. Check
https://ollama.com/search?c=tools for the current tool-capable list.
"""

from __future__ import annotations

import os
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_ollama import ChatOllama

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
    tools = cosmergon_tools(player_token=os.environ["COSMERGON_PLAYER_TOKEN"])

    # Model-agnostic: same tools work with local Ollama
    llm = ChatOllama(
        model="llama3.2:3b",  # Or qwen2.5:7b, mistral-nemo, phi4, etc.
        temperature=0.2,
        base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    ).bind_tools(tools)

    answer = run_with_tools(
        llm,
        tools,
        "Check my Cosmergon state. If energy balance is over 1500, "
        "describe what I could do next in 2 sentences. No actions yet — "
        "just observe.",
    )

    print("LLM response:")
    print(answer)


if __name__ == "__main__":
    main()
