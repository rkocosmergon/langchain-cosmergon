"""Cosmergon tools for LangChain-compatible agent frameworks.

Wraps Cosmergon REST API as LangChain @tool-decorated functions. Works with
LangChain, CrewAI (identical Tool-interface), and any framework that
consumes LangChain tools.

Usage::

    from langchain_cosmergon import cosmergon_tools

    # Single-agent, API-key mode:
    tools = cosmergon_tools(api_key="AGENT-...:secret")

    # Multi-agent, master-key mode (recommended for advanced use):
    tools = cosmergon_tools(player_token="CSMR-...", agent_name="Odin-scout")

Note: Requires ``langchain-core`` installed separately — we don't pin it
  to avoid version conflicts with your other LangChain deps.
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import httpx

from langchain_cosmergon.exceptions import (
    ApiUnavailableError,
    AuthenticationError,
    ConfigurationError,
    InvalidActionError,
    RateLimitError,
)
from langchain_cosmergon.version import __version__

# Same default as cosmergon-agent SDK and cosmergon-pet — cosmergon.com is the
# canonical Caddy-served origin (api.cosmergon.com resolves via DNS but has no
# virtual host on the Caddy reverse proxy → connection failure).
# Previously "https://api.cosmergon.com" → TLS-handshake failed for users who
# didn't set base_url explicitly. Fixed in v0.1.1.
DEFAULT_BASE_URL = "https://cosmergon.com"


def _get_client(api_key: str | None = None, base_url: str = DEFAULT_BASE_URL) -> httpx.Client:
    """Create a sync HTTP client with TLS + SDK identification headers.

    Every game route takes the agent's API key. A master key is exchanged for one first
    (``_resolve_master_key``).
    """
    if api_key is None:
        raise ConfigurationError(
            "Neither api_key nor player_token provided. "
            "Set COSMERGON_PLAYER_TOKEN env var or pass player_token='CSMR-...' "
            "explicitly. See https://cosmergon.com/getting-started."
        )
    headers = {
        "User-Agent": f"langchain-cosmergon/{__version__}",
        "X-Cosmergon-Client-Type": f"langchain-cosmergon/{__version__}",
        "Authorization": f"api-key {api_key}",
    }
    return httpx.Client(base_url=base_url, headers=headers, timeout=30.0, verify=True)


def _get(client: httpx.Client, path: str) -> httpx.Response:
    """GET with the connection failures turned into ``ApiUnavailableError``."""
    try:
        return client.get(path)
    except httpx.ConnectError as exc:
        raise ApiUnavailableError(
            f"Could not connect to Cosmergon API at {client.base_url}. "
            "Check your network connection and https://cosmergon.com/status."
        ) from exc
    except httpx.TimeoutException as exc:
        raise ApiUnavailableError(
            "Cosmergon API request timed out after 30 seconds. "
            "Retry or check https://cosmergon.com/status."
        ) from exc


def _resolve_master_key(
    player_token: str, agent_name: str | None, base_url: str
) -> tuple[str, str]:
    """Exchange the master key for one agent's API key and id, as the Cosmergon SDK does.

    The server takes a master key only at ``GET /api/v1/players/me/agents`` under
    ``X-Player-Token`` and answers with a fresh API key per agent; every other route wants
    ``Authorization: api-key ...``. Up to 0.2.0 this package sent the master key as
    ``X-Cosmergon-Player-Token`` to ``/agents/``, a header the server does not read: the
    master-key mode failed with 401 on every account (cos20 #587).
    """
    headers = {
        "User-Agent": f"langchain-cosmergon/{__version__}",
        "X-Cosmergon-Client-Type": f"langchain-cosmergon/{__version__}",
        "X-Player-Token": player_token,
    }
    with httpx.Client(base_url=base_url, headers=headers, timeout=30.0, verify=True) as client:
        data = _handle_response(_get(client, "/api/v1/players/me/agents"))
    agents = data.get("agents") if isinstance(data, dict) else None
    if not agents:
        raise ConfigurationError(
            "No Cosmergon agents found for this account. "
            "Register your first agent via the Cosmergon SDK or at "
            "https://cosmergon.com/getting-started."
        )
    chosen = agents[0]  # the oldest, as in the SDK
    if agent_name:
        named = [a for a in agents if a.get("agent_name") == agent_name]
        if not named:
            raise ConfigurationError(
                f"Agent '{agent_name}' not found in your account. "
                f"Available agents: {[a.get('agent_name') for a in agents]}"
            )
        chosen = named[0]
    return str(chosen["api_key"]), str(chosen["agent_id"])


def _handle_response(resp: httpx.Response) -> dict[str, Any]:
    """Translate HTTP response into typed exception or JSON payload.

    Every failure path carries an actionable message for LangChain users —
    no bare stack-traces. Message includes link to documentation.
    """
    if resp.status_code == 200 or resp.status_code == 201:
        try:
            return resp.json()
        except json.JSONDecodeError as exc:
            raise ApiUnavailableError(
                f"Cosmergon API returned non-JSON response (status {resp.status_code}). "
                f"This is unusual — check https://cosmergon.com/status or retry in 30s. "
                f"Raw body: {resp.text[:200]}"
            ) from exc

    if resp.status_code == 401 or resp.status_code == 403:
        raise AuthenticationError(
            "Cosmergon rejected your credentials (HTTP "
            f"{resp.status_code}). "
            "Check your COSMERGON_PLAYER_TOKEN (must start with 'CSMR-') or "
            "regenerate at https://cosmergon.com/settings."
        )

    if resp.status_code == 429:
        retry = int(resp.headers.get("Retry-After", "60"))
        raise RateLimitError(
            f"Cosmergon rate-limit exceeded. Wait {retry}s or upgrade "
            "at https://cosmergon.com/pricing.",
            retry_after_seconds=retry,
        )

    if resp.status_code == 422 or resp.status_code == 400:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:200])
        except Exception:
            detail = resp.text[:200]
        raise InvalidActionError(
            f"Cosmergon rejected the action (HTTP {resp.status_code}): {detail}. "
            "Check the action parameters or your current game state at "
            "https://cosmergon.com/getting-started#actions."
        )

    if resp.status_code >= 500:
        raise ApiUnavailableError(
            f"Cosmergon API error (HTTP {resp.status_code}). "
            "Check https://cosmergon.com/status. If persistent, report at "
            "https://github.com/rkocosmergon/langchain-cosmergon/issues."
        )

    raise ApiUnavailableError(
        f"Cosmergon API returned unexpected status {resp.status_code}. Body: {resp.text[:200]}"
    )


def _resolve_agent_id(client: httpx.Client, agent_name: str | None = None) -> str:
    """Resolve agent_id from the auth context (api_key mode).

    - If ``agent_name`` given: lookup the specific agent
    - Otherwise: first agent in the list
    """
    data = _handle_response(_get(client, "/api/v1/agents/"))
    agents = data if isinstance(data, list) else data.get("agents", [])

    if not agents:
        raise ConfigurationError(
            "No Cosmergon agents found for this account. "
            "Register your first agent via the Cosmergon SDK or at "
            "https://cosmergon.com/getting-started."
        )

    if agent_name:
        for a in agents:
            if a.get("name") == agent_name or a.get("username") == agent_name:
                return str(a["id"])
        raise ConfigurationError(
            f"Agent '{agent_name}' not found in your account. "
            f"Available agents: {[a.get('name') for a in agents]}"
        )

    return str(agents[0]["id"])


def _make_observe_tool(tool_decorator: Any, client: httpx.Client, agent_id: str) -> Any:
    @tool_decorator
    def cosmergon_observe(detail: str = "summary") -> str:
        """Get your Cosmergon agent's current game state.

        Args:
            detail: "summary" (basic) or "rich" (full context — available
              on every tier, including free).
        """
        resp = client.get(f"/api/v1/agents/{agent_id}/state", params={"detail": detail})
        return json.dumps(_handle_response(resp), indent=2)

    return cosmergon_observe


def _make_act_tool(tool_decorator: Any, client: httpx.Client, agent_id: str) -> Any:
    @tool_decorator
    def cosmergon_act(action: str, params: str = "{}") -> str:
        """Execute a Cosmergon game action.

        Args:
            action: e.g. ``place_cells``, ``create_field``, ``evolve``,
              ``transfer_energy``, ``market_list``, ``market_buy``,
              ``start_mission``. Call ``cosmergon_info`` for the live list —
              actions carry an ``available`` flag and can be turned off by
              world configuration.
            params: JSON string of action-specific parameters.
        """
        try:
            parsed = {k: v for k, v in json.loads(params).items() if k != "action"}
        except json.JSONDecodeError as exc:
            raise InvalidActionError(f"`params` must be valid JSON. Got: {params[:100]}") from exc

        body = {"action": action, **parsed}
        resp = client.post(
            f"/api/v1/agents/{agent_id}/action",
            json=body,
            headers={"X-Idempotency-Key": str(uuid.uuid4())},
        )
        return json.dumps(_handle_response(resp), indent=2)

    return cosmergon_act


def _make_benchmark_tool(tool_decorator: Any, client: httpx.Client, agent_id: str) -> Any:
    @tool_decorator
    def cosmergon_benchmark(days: int = 7) -> str:
        """Generate a benchmark report for your agent.

        Returns a 6-dimension performance report comparing your agent
        against all other active agents over the given period.

        Args:
            days: Benchmark period in days (1–90).
        """
        if not 1 <= days <= 90:
            raise InvalidActionError(f"`days` must be between 1 and 90, got {days}.")
        resp = client.get(
            f"/api/v1/benchmark/{agent_id}/report",
            params={"days": days},
        )
        return json.dumps(_handle_response(resp), indent=2)

    return cosmergon_benchmark


def _make_info_tool(tool_decorator: Any, client: httpx.Client) -> Any:
    @tool_decorator
    def cosmergon_info() -> str:
        """Get Cosmergon game rules, economy parameters, and live metrics."""
        info_resp = client.get("/api/v1/game/info")
        info = _handle_response(info_resp)
        metrics_resp = client.get("/api/v1/game/metrics")
        metrics = _handle_response(metrics_resp)
        return json.dumps({"rules": info, "metrics": metrics}, indent=2)

    return cosmergon_info


def _make_contracts_tool(tool_decorator: Any, client: httpx.Client, agent_id: str) -> Any:
    """S204 — the full contract suite (propose/accept/reject/counter/apply/decide).

    Kept in sync with ``cosmergon_agent.integrations.langchain``; contracts are
    the mechanic where agents negotiate with each other, so a tool list without
    them hides half the game.
    """

    @tool_decorator
    def cosmergon_contracts(operation: str, params: str = "{}") -> str:
        """Cosmergon contract operations.

        Args:
            operation: One of:
                'list_templates' (no params) — the T01-T10 standard templates
                'list_pending' (no params) — proposals addressed to me
                'propose_from_template' {template_id, slots, mode?='targeted', escrow?=0}
                'propose' {to_player_id, contract_type, terms, escrow_amount?=0}
                'accept' {contract_id, escrow_amount?=0}
                'reject' {contract_id, reason?=null}
                'counter' {contract_id, slots, escrow?=0} — max 3 rounds
                'breach' {contract_id} — loses escrow
                'apply' {contract_id, counter_slots?=null} — open-call apply
                'decide' {contract_id, application_id, decision, reason?=null}
            params: JSON string with the operation-specific args.
        """
        try:
            p = json.loads(params) if params else {}
        except json.JSONDecodeError as exc:
            raise InvalidActionError(f"`params` must be valid JSON. Got: {params[:100]}") from exc

        if operation == "list_templates":
            return json.dumps(_handle_response(client.get("/api/v1/contracts/templates")), indent=2)
        if operation == "list_pending":
            state = _handle_response(client.get(f"/api/v1/agents/{agent_id}/state"))
            return json.dumps(state.get("contracts", {}).get("pending_inbound", []) or [], indent=2)

        action_map = {
            "propose": "propose_contract",
            "propose_from_template": "propose_from_template",
            "accept": "accept_contract",
            "reject": "reject_contract",
            "counter": "propose_counter",
            "breach": "breach_contract",
            "apply": "apply_to_contract",
            "decide": "decide_application",
        }
        action = action_map.get(operation)
        if not action:
            bekannt = sorted([*action_map, "list_templates", "list_pending"])
            raise InvalidActionError(f"unknown operation '{operation}'. Known: {bekannt}")
        resp = client.post(
            f"/api/v1/agents/{agent_id}/action",
            # As in the act tool, the mapped action wins over an "action" key (cos20 #587).
            json={"action": action, **{k: v for k, v in p.items() if k != "action"}},
            headers={"X-Idempotency-Key": str(uuid.uuid4())},
        )
        return json.dumps(_handle_response(resp), indent=2)

    return cosmergon_contracts


def cosmergon_tools(
    api_key: str | None = None,
    player_token: str | None = None,
    agent_name: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> list[Any]:
    """Create LangChain-compatible tools for Cosmergon.

    Args:
        api_key: Direct agent API-key (``AGENT-<id>:<secret>``). Mutually
          exclusive with ``player_token``.
        player_token: Master key (``CSMR-...``, Solo+ feature). Allows
          multi-agent access. Mutually exclusive with ``api_key``.
        agent_name: Required if ``player_token`` given and account has
          multiple agents. Otherwise first agent is used.
        base_url: Override for dev/staging (default: production).

    Returns:
        List of LangChain ``Tool`` objects ready to pass to an agent executor.

    Raises:
        ConfigurationError: if credentials missing or agent not found.
        ApiUnavailableError: if Cosmergon API unreachable at init time.
    """
    # Env-var fallback
    if api_key is None and player_token is None:
        api_key = os.environ.get("COSMERGON_API_KEY")
        player_token = os.environ.get("COSMERGON_PLAYER_TOKEN")

    try:
        from langchain_core.tools import tool  # noqa: F401
    except ImportError as exc:
        raise ConfigurationError(
            "langchain-core is required. Install with: pip install langchain-core"
        ) from exc

    if api_key is None and player_token is not None:
        api_key, agent_id = _resolve_master_key(player_token, agent_name, base_url)
        client = _get_client(api_key, base_url=base_url)
    else:
        client = _get_client(api_key, base_url=base_url)
        agent_id = _resolve_agent_id(client, agent_name=agent_name)

    return [
        _make_observe_tool(tool, client, agent_id),
        _make_act_tool(tool, client, agent_id),
        _make_benchmark_tool(tool, client, agent_id),
        _make_info_tool(tool, client),
        _make_contracts_tool(tool, client, agent_id),
    ]
