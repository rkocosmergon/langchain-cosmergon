"""Guards cos20 #587: contracts action key, master key, examples, README, publish workflow."""

from __future__ import annotations

import functools
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import httpx
import pytest

from langchain_cosmergon.exceptions import ConfigurationError
from langchain_cosmergon.tools import _make_contracts_tool, cosmergon_tools


def test_contracts_tool_sends_the_mapped_action() -> None:
    """operation "accept" stays accept_contract even if params carry an "action" key, as in
    the act tool."""
    sent: list[dict] = []

    def answer(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"success": True})

    client = httpx.Client(base_url="https://cosmergon.com", transport=httpx.MockTransport(answer))
    tool = _make_contracts_tool(lambda f: f, client, "a1")
    tool("accept", json.dumps({"contract_id": "c1", "action": "breach_contract"}))
    assert [body["action"] for body in sent] == ["accept_contract"]


# --- cos20 #587, second round: master key, examples, README, publish workflow -----------------

MASTER = "CSMR-" + "0" * 32
KEYS = {"a1": "AGENT-a1:alpha-secret", "b2": "AGENT-b2:beta-secret"}
REPO = Path(__file__).resolve().parents[1]


def _server(seen: list[httpx.Request]) -> httpx.MockTransport:
    """Answers like the production server: the master key counts only at
    /players/me/agents under X-Player-Token, every other route wants an agent's api-key."""

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path
        if path == "/api/v1/players/me/agents":
            if request.headers.get("X-Player-Token") != MASTER:
                return httpx.Response(401, json={"error": {"message": "Missing X-Player-Token"}})
            agents = [
                {"agent_id": "a1", "agent_name": "Alpha", "api_key": KEYS["a1"]},
                {"agent_id": "b2", "agent_name": "Beta", "api_key": KEYS["b2"]},
            ]
            return httpx.Response(200, json={"player_id": "p1", "agents": agents})
        auth = request.headers.get("Authorization", "")
        agent = next((a for a, k in KEYS.items() if auth == f"api-key {k}"), None)
        if agent is None:
            return httpx.Response(401, json={"error": {"message": "No authorization"}})
        if path == "/api/v1/agents/":
            return httpx.Response(200, json=[{"id": agent, "username": agent}])
        if path == f"/api/v1/agents/{agent}/state":
            return httpx.Response(200, json={"agent_id": agent, "energy": 100})
        if path == f"/api/v1/agents/{agent}/action":
            return httpx.Response(200, json={"success": True, "agent_id": agent})
        if path == f"/api/v1/benchmark/{agent}/report":
            return httpx.Response(200, json=BERICHT)
        return httpx.Response(404, json={"error": {"message": "not found"}})

    return httpx.MockTransport(answer)


@pytest.fixture
def seen(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    """Every httpx.Client the package builds talks to the production-like fake server."""
    requests: list[httpx.Request] = []
    real = httpx.Client
    monkeypatch.setattr(httpx, "Client", functools.partial(real, transport=_server(requests)))
    return requests


def test_master_key_plays_the_named_agent(seen: list[httpx.Request]) -> None:
    """player_token mode: the master key is exchanged at /players/me/agents, the moves go
    out under the named agent's api-key (up to 0.2.0: 401 on every account)."""
    tools = cosmergon_tools(player_token=MASTER, agent_name="Beta")
    act = next(t for t in tools if t.name == "cosmergon_act")
    act.invoke({"action": "place_cells", "params": "{}"})
    move = seen[-1]
    assert move.url.path == "/api/v1/agents/b2/action"
    assert move.headers["Authorization"] == f"api-key {KEYS['b2']}"
    assert all("X-Cosmergon-Player-Token" not in r.headers for r in seen)


def test_master_key_without_name_plays_the_first_agent(seen: list[httpx.Request]) -> None:
    tools = cosmergon_tools(player_token=MASTER)
    observe = next(t for t in tools if t.name == "cosmergon_observe")
    observe.invoke({"detail": "summary"})
    assert seen[-1].url.path == "/api/v1/agents/a1/state"


def test_master_key_with_unknown_name_says_so(seen: list[httpx.Request]) -> None:
    with pytest.raises(ConfigurationError, match="Gamma"):
        cosmergon_tools(player_token=MASTER, agent_name="Gamma")


class _Model:
    """A tool-calling chat model: asks for cosmergon_observe once, then answers in text."""

    def __init__(self, **_: object) -> None:
        self.calls = 0

    def bind_tools(self, _tools: object) -> _Model:
        return self

    def invoke(self, _messages: object) -> SimpleNamespace:
        self.calls += 1
        if self.calls == 1:
            ask = {"name": "cosmergon_observe", "args": {"detail": "summary"}, "id": "c1"}
            return SimpleNamespace(content="", tool_calls=[ask])
        return SimpleNamespace(content="done", tool_calls=[])


def _load_example(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, REPO / "examples" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_llm_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "langchain_openai", SimpleNamespace(ChatOpenAI=_Model))
    monkeypatch.setitem(sys.modules, "langchain_ollama", SimpleNamespace(ChatOllama=_Model))
    monkeypatch.setenv("COSMERGON_PLAYER_TOKEN", MASTER)


@pytest.mark.parametrize(
    "example", ["01_profit_maximizer", "02_coordinated_agents", "04_local_ollama"]
)
def test_examples_execute_the_requested_tool_calls(
    example: str, seen: list[httpx.Request], monkeypatch: pytest.MonkeyPatch
) -> None:
    """bind_tools(...).invoke only returns the calls; the examples have to run them."""
    _fake_llm_modules(monkeypatch)
    module = _load_example(example)
    monkeypatch.setattr(module, "cosmergon_tools", _named_alpha)
    if hasattr(module, "time"):
        monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    module.main()
    assert any(r.url.path.endswith("/state") for r in seen)


def _named_alpha(**kwargs: object) -> list:
    """Example 02 asks for "scout" and "trader"; the fake account has Alpha and Beta."""
    return cosmergon_tools(player_token=MASTER, agent_name="Alpha")


def test_readme_quickstart_executes_the_requested_tool_calls(
    seen: list[httpx.Request], monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_llm_modules(monkeypatch)
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    quickstart = readme.split("```python\n", 1)[1].split("```", 1)[0]
    exec(compile(quickstart, "README.md quickstart", "exec"), {"__name__": "quickstart"})  # noqa: S102
    assert any(r.url.path == "/api/v1/agents/a1/state" for r in seen)


BERICHT = {
    "overall_rank": 3,
    "overall_percentile": 90,
    "total_agents": 30,
    "is_alive": True,
    "current_balance": 1200,
    "actual_data_hours": 168,
    "applicable_dims_count": 6,
    "share_url": "https://cosmergon.com/b/x",
    "agent_id": "a1",
    "agent_name": "Alpha",
    "persona": "trader",
    "report_date": "2026-10-27",
    "benchmark_duration_days": 7,
    "agent_active_since": "2026-10-01",
    "benchmark_context": "",
    "scores": [
        {
            "name": "growth",
            "value": 0.7,
            "rank": 2,
            "total_agents": 30,
            "percentile": 93,
            "detail": "grows fast",
            "is_applicable": True,
            "value_unit": "ratio",
        }
    ],
    "strengths": ["growth"],
    "weaknesses": ["trade"],
    "recommendations": ["sell more"],
    "summary": "",
    "schema_version": "1",
    "persona_description": "",
    "tier_gate": "solo",
}


def test_example_03_prints_the_report_fields(
    seen: list[httpx.Request], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """Keys as in the server's BenchmarkBericht (cos20 schemas/agent_auskunft.py)."""
    monkeypatch.setenv("COSMERGON_PLAYER_TOKEN", MASTER)
    _load_example("03_benchmark_report").main()
    out = capsys.readouterr().out
    assert "Agent: Alpha" in out and "Persona: trader" in out
    assert "growth: 0.7" in out and "grows fast" in out
    assert "['trade']" in out and "['sell more']" in out


def test_publish_installs_twine_before_twine_check() -> None:
    """The 'twine check' step came without twine in the install step (cos20 #587)."""
    workflow = (REPO / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    install, rest = workflow.split("- name: Build package", 1)
    assert "twine check" in rest
    assert "twine" in install.split("- name: Install build tools", 1)[1]
