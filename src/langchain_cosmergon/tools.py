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


def _get_client(
    api_key: str | None = None,
    player_token: str | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> httpx.Client:
    """Create a sync HTTP client with TLS + SDK identification headers."""
    headers = {
        "User-Agent": f"langchain-cosmergon/{__version__}",
        "X-Cosmergon-Client-Type": f"langchain-cosmergon/{__version__}",
    }
    if api_key is not None:
        headers["Authorization"] = f"api-key {api_key}"
    elif player_token is not None:
        headers["X-Cosmergon-Player-Token"] = player_token
    else:
        raise ConfigurationError(
            "Neither api_key nor player_token provided. "
            "Set COSMERGON_PLAYER_TOKEN env var or pass player_token='CSMR-...' "
            "explicitly. See https://cosmergon.com/getting-started."
        )
    return httpx.Client(base_url=base_url, headers=headers, timeout=30.0, verify=True)


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
            "at https://cosmergon.com/pricing. "
            "(LangChain starter-tier gives 120 req/min for 30 days — activate by "
            "registering a fresh agent via this package.)",
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
    """Resolve agent_id from the auth context.

    - If ``agent_name`` given (player_token mode): lookup the specific agent
    - Otherwise (api_key mode): first agent in the list
    """
    try:
        resp = client.get("/api/v1/agents/")
    except httpx.ConnectError as exc:
        raise ApiUnavailableError(
            "Could not connect to Cosmergon API at api.cosmergon.com. "
            "Check your network connection and https://cosmergon.com/status."
        ) from exc
    except httpx.TimeoutException as exc:
        raise ApiUnavailableError(
            "Cosmergon API request timed out after 30 seconds. "
            "Retry or check https://cosmergon.com/status."
        ) from exc

    data = _handle_response(resp)
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
            detail: "summary" (basic) or "rich" (full context — requires
              Solo+ tier or active LangChain starter-tier).
        """
        resp = client.get(f"/api/v1/agents/{agent_id}/state", params={"detail": detail})
        return json.dumps(_handle_response(resp), indent=2)

    return cosmergon_observe


def _make_act_tool(tool_decorator: Any, client: httpx.Client, agent_id: str) -> Any:
    @tool_decorator
    def cosmergon_act(action: str, params: str = "{}") -> str:
        """Execute a Cosmergon game action.

        Args:
            action: e.g. ``place_cells``, ``create_field``, ``create_cube``,
              ``evolve``, ``transfer_energy``, ``market_list``, ``market_buy``.
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

    client = _get_client(api_key=api_key, player_token=player_token, base_url=base_url)
    agent_id = _resolve_agent_id(client, agent_name=agent_name)

    return [
        _make_observe_tool(tool, client, agent_id),
        _make_act_tool(tool, client, agent_id),
        _make_benchmark_tool(tool, client, agent_id),
        _make_info_tool(tool, client),
    ]
