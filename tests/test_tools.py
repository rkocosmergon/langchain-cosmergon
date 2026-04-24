"""Integration tests for the four Cosmergon tool functions.

Uses httpx.MockTransport to test tool wiring end-to-end without a live
backend. This gives us confidence that the tools actually pass correct
arguments, read correct endpoints, and return correct JSON.
"""

from __future__ import annotations

import json
import uuid

import httpx
import pytest

from langchain_cosmergon.exceptions import (
    ApiUnavailableError,
    AuthenticationError,
    ConfigurationError,
    InvalidActionError,
)
from langchain_cosmergon.tools import (
    _get_client,
    _make_act_tool,
    _make_benchmark_tool,
    _make_info_tool,
    _make_observe_tool,
    _resolve_agent_id,
)

# -------------------------------------------------------------------
# Shared fixtures
# -------------------------------------------------------------------


AGENT_ID = str(uuid.uuid4())


def _mock_handler(routes: dict[tuple[str, str], httpx.Response]):
    """Return an httpx mock-transport that dispatches by (method, path)."""

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key not in routes:
            return httpx.Response(404, json={"error": {"message": f"no route for {key}"}})
        return routes[key]

    return httpx.MockTransport(handler)


def _fake_client(routes: dict) -> httpx.Client:
    return httpx.Client(
        transport=_mock_handler(routes),
        base_url="https://api.example.test",
        headers={"Authorization": "api-key test"},
    )


def _mock_tool_decorator():
    """Fake LangChain @tool decorator — returns the raw function for testing."""

    def decorator(fn):
        return fn

    return decorator


# -------------------------------------------------------------------
# _get_client — credential validation
# -------------------------------------------------------------------


class TestGetClient:
    def test_missing_credentials_raises_configuration_error(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            _get_client()
        assert "COSMERGON_PLAYER_TOKEN" in str(exc_info.value)

    def test_api_key_sets_authorization_header(self) -> None:
        client = _get_client(api_key="AGENT-123:secret")
        assert client.headers["Authorization"] == "api-key AGENT-123:secret"
        assert "langchain-cosmergon" in client.headers["User-Agent"]
        assert client.headers["X-Cosmergon-Client-Type"].startswith("langchain-cosmergon/")

    def test_player_token_sets_master_key_header(self) -> None:
        client = _get_client(player_token="CSMR-testtoken")
        assert client.headers["X-Cosmergon-Player-Token"] == "CSMR-testtoken"
        assert "Authorization" not in client.headers


# -------------------------------------------------------------------
# _resolve_agent_id — single-agent and multi-agent modes
# -------------------------------------------------------------------


class TestResolveAgentId:
    def test_single_agent_list_returns_first(self) -> None:
        client = _fake_client(
            {
                ("GET", "/api/v1/agents/"): httpx.Response(
                    200, json=[{"id": AGENT_ID, "name": "scout"}]
                )
            }
        )
        assert _resolve_agent_id(client) == AGENT_ID

    def test_multi_agent_with_name_filter(self) -> None:
        client = _fake_client(
            {
                ("GET", "/api/v1/agents/"): httpx.Response(
                    200,
                    json=[
                        {"id": "other-id", "name": "scout"},
                        {"id": AGENT_ID, "name": "trader"},
                    ],
                )
            }
        )
        assert _resolve_agent_id(client, agent_name="trader") == AGENT_ID

    def test_no_agents_raises_configuration_error(self) -> None:
        client = _fake_client({("GET", "/api/v1/agents/"): httpx.Response(200, json=[])})
        with pytest.raises(ConfigurationError) as exc_info:
            _resolve_agent_id(client)
        assert "getting-started" in str(exc_info.value)

    def test_agent_name_not_found_raises_with_hint(self) -> None:
        client = _fake_client(
            {
                ("GET", "/api/v1/agents/"): httpx.Response(
                    200, json=[{"id": "id-1", "name": "scout"}]
                )
            }
        )
        with pytest.raises(ConfigurationError) as exc_info:
            _resolve_agent_id(client, agent_name="nonexistent")
        assert "scout" in str(exc_info.value)

    def test_401_raises_authentication_error(self) -> None:
        client = _fake_client(
            {("GET", "/api/v1/agents/"): httpx.Response(401, json={"error": "bad key"})}
        )
        with pytest.raises(AuthenticationError):
            _resolve_agent_id(client)


# -------------------------------------------------------------------
# Tool factories — cosmergon_observe, _act, _benchmark, _info
# -------------------------------------------------------------------


class TestObserveTool:
    def test_observe_returns_json_string(self) -> None:
        client = _fake_client(
            {
                (
                    "GET",
                    f"/api/v1/agents/{AGENT_ID}/state",
                ): httpx.Response(200, json={"energy": 1500, "fields": 3})
            }
        )
        tool = _make_observe_tool(_mock_tool_decorator(), client, AGENT_ID)
        result = tool(detail="summary")
        parsed = json.loads(result)
        assert parsed["energy"] == 1500

    def test_observe_propagates_auth_error(self) -> None:
        client = _fake_client(
            {
                (
                    "GET",
                    f"/api/v1/agents/{AGENT_ID}/state",
                ): httpx.Response(401, json={})
            }
        )
        tool = _make_observe_tool(_mock_tool_decorator(), client, AGENT_ID)
        with pytest.raises(AuthenticationError):
            tool()


class TestActTool:
    def test_act_sends_idempotency_key(self) -> None:
        captured_headers: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_headers.update(dict(request.headers))
            return httpx.Response(200, json={"success": True})

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://api.example.test",
        )
        tool = _make_act_tool(_mock_tool_decorator(), client, AGENT_ID)
        tool(action="place_cells", params='{"field_id": "abc", "cells": [[1,2]]}')
        assert "x-idempotency-key" in captured_headers

    def test_act_rejects_invalid_json(self) -> None:
        client = _fake_client({})
        tool = _make_act_tool(_mock_tool_decorator(), client, AGENT_ID)
        with pytest.raises(InvalidActionError) as exc_info:
            tool(action="test", params="not-json")
        assert "valid JSON" in str(exc_info.value)

    def test_act_propagates_422(self) -> None:
        client = _fake_client(
            {
                (
                    "POST",
                    f"/api/v1/agents/{AGENT_ID}/action",
                ): httpx.Response(
                    422,
                    json={
                        "error": {
                            "code": 422,
                            "message": "Not enough energy",
                            "type": "http_error",
                        }
                    },
                )
            }
        )
        tool = _make_act_tool(_mock_tool_decorator(), client, AGENT_ID)
        with pytest.raises(InvalidActionError) as exc_info:
            tool(action="create_field", params="{}")
        assert "Not enough energy" in str(exc_info.value)


class TestBenchmarkTool:
    def test_benchmark_defaults_to_7_days(self) -> None:
        captured_params: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured_params.update(dict(request.url.params))
            return httpx.Response(200, json={"scores": []})

        client = httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://api.example.test",
        )
        tool = _make_benchmark_tool(_mock_tool_decorator(), client, AGENT_ID)
        tool()
        assert captured_params.get("days") == "7"

    def test_benchmark_rejects_out_of_range_days(self) -> None:
        client = _fake_client({})
        tool = _make_benchmark_tool(_mock_tool_decorator(), client, AGENT_ID)
        with pytest.raises(InvalidActionError):
            tool(days=0)
        with pytest.raises(InvalidActionError):
            tool(days=91)

    def test_benchmark_custom_days(self) -> None:
        client = _fake_client(
            {
                (
                    "GET",
                    f"/api/v1/benchmark/{AGENT_ID}/report",
                ): httpx.Response(
                    200, json={"scores": [{"dimension": "exploration", "value": 0.7}]}
                )
            }
        )
        tool = _make_benchmark_tool(_mock_tool_decorator(), client, AGENT_ID)
        result = json.loads(tool(days=30))
        assert len(result["scores"]) == 1


class TestInfoTool:
    def test_info_combines_rules_and_metrics(self) -> None:
        client = _fake_client(
            {
                ("GET", "/api/v1/game/info"): httpx.Response(200, json={"max_agents": 80}),
                ("GET", "/api/v1/game/metrics"): httpx.Response(200, json={"fs_ratio": 1.15}),
            }
        )
        tool = _make_info_tool(_mock_tool_decorator(), client)
        result = json.loads(tool())
        assert result["rules"]["max_agents"] == 80
        assert result["metrics"]["fs_ratio"] == 1.15

    def test_info_propagates_503(self) -> None:
        client = _fake_client(
            {
                ("GET", "/api/v1/game/info"): httpx.Response(503, json={}),
                ("GET", "/api/v1/game/metrics"): httpx.Response(200, json={}),
            }
        )
        tool = _make_info_tool(_mock_tool_decorator(), client)
        with pytest.raises(ApiUnavailableError):
            tool()
