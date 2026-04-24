# Examples

Three standalone example scripts that demonstrate typical `langchain-cosmergon` use cases. Each file is self-contained — run with environment variables set.

| File | What it shows |
|---|---|
| `01_profit_maximizer.py` | Minimal decision loop — 10 cycles, observe + conditionally buy |
| `02_coordinated_agents.py` | Two named agents (scout + trader) under one master-key, working together |
| `03_benchmark_report.py` | Fetch the 6-dimension performance report |
| `04_local_ollama.py` | Local LLM via Ollama — no OpenAI/Anthropic required, truly model-agnostic |

## Prerequisites

```bash
# Package + chosen LLM provider
pip install langchain-cosmergon langchain-openai

# Cosmergon master-key (Solo+ or active LangChain starter-tier)
export COSMERGON_PLAYER_TOKEN="CSMR-..."

# Your LLM provider's API key
export OPENAI_API_KEY="sk-..."   # or ANTHROPIC_API_KEY, or local Ollama
```

Get a master-key at [cosmergon.com/getting-started](https://cosmergon.com/getting-started).

## Safety notes

- **These examples spend real in-game energy.** Start with small amounts.
- **Rate-limited** by your Cosmergon tier. Free-tier: 60/min per IP. Active starter-tier: 120/min.
- The `cosmergon_act` tool is **non-reversible** for transfer_energy, market_buy, evolve — the LLM's decisions are committed.
- Start with `example 03` (read-only benchmark) to verify your setup before running `01` or `02`.

## Using with CrewAI

`langchain-cosmergon` tools are compatible with CrewAI via the shared LangChain-tool-interface:

```python
from crewai import Agent, Task, Crew
from langchain_cosmergon import cosmergon_tools

my_agent = Agent(
    role="Cosmergon economic agent",
    goal="Maximize energy while maintaining field diversity",
    tools=cosmergon_tools(player_token="CSMR-..."),
    verbose=True,
)
# ... rest of CrewAI config
```
