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

from langchain_ollama import ChatOllama

from langchain_cosmergon import cosmergon_tools


def main() -> None:
    tools = cosmergon_tools(player_token=os.environ["COSMERGON_PLAYER_TOKEN"])

    # Model-agnostic: same tools work with local Ollama
    llm = ChatOllama(
        model="llama3.2:3b",  # Or qwen2.5:7b, mistral-nemo, phi4, etc.
        temperature=0.2,
        base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    ).bind_tools(tools)

    response = llm.invoke(
        "Check my Cosmergon state. If energy balance is over 1500, "
        "describe what I could do next in 2 sentences. No actions yet — "
        "just observe."
    )

    print("LLM response:")
    print(response.content if hasattr(response, "content") else response)


if __name__ == "__main__":
    main()
