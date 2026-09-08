"""The contract suite (S204) — the mechanic where agents negotiate with agents.

The tool list shipped four tools while the SDK integration shipped five; a
LangChain user could observe, act, benchmark and read info, but could not take
part in a single contract. Same mock-transport wiring as ``test_tools.py``.
"""

from __future__ import annotations

import json
import uuid

import httpx
import pytest

from langchain_cosmergon.exceptions import InvalidActionError
from langchain_cosmergon.tools import _make_contracts_tool

AGENT_ID = str(uuid.uuid4())


def _fake_client(routes: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key not in routes:
            return httpx.Response(404, json={"error": {"message": f"no route for {key}"}})
        return routes[key]

    return httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://api.example.test",
        headers={"Authorization": "api-key test"},
    )


def _decorator():
    def deko(fn):
        return fn

    return deko


def test_list_templates_geht_an_den_template_endpunkt() -> None:
    client = _fake_client(
        {("GET", "/api/v1/contracts/templates"): httpx.Response(200, json=[{"id": "T01"}])}
    )
    tool = _make_contracts_tool(_decorator(), client, AGENT_ID)

    assert json.loads(tool("list_templates")) == [{"id": "T01"}]


def test_list_pending_liest_den_state_und_filtert_den_posteingang() -> None:
    client = _fake_client(
        {
            ("GET", f"/api/v1/agents/{AGENT_ID}/state"): httpx.Response(
                200, json={"contracts": {"pending_inbound": [{"id": "c-1"}]}}
            )
        }
    )
    tool = _make_contracts_tool(_decorator(), client, AGENT_ID)

    assert json.loads(tool("list_pending")) == [{"id": "c-1"}]


def test_operation_wird_auf_die_action_abgebildet() -> None:
    """`accept` muss als `accept_contract` an den Action-Endpunkt gehen."""
    gesehen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        gesehen.update(json.loads(request.content))
        gesehen["idempotency"] = request.headers.get("X-Idempotency-Key")
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://api.example.test"
    )
    tool = _make_contracts_tool(_decorator(), client, AGENT_ID)

    tool("accept", json.dumps({"contract_id": "c-9", "escrow_amount": 500}))

    assert gesehen["action"] == "accept_contract"
    assert gesehen["contract_id"] == "c-9"
    assert gesehen["escrow_amount"] == 500
    assert gesehen["idempotency"], "Vertrags-Aktionen brauchen einen Idempotency-Key"


def test_unbekannte_operation_wirft_statt_still_zu_scheitern() -> None:
    client = _fake_client({})
    tool = _make_contracts_tool(_decorator(), client, AGENT_ID)

    with pytest.raises(InvalidActionError) as exc:
        tool("kaufe_alles")
    assert "kaufe_alles" in str(exc.value)


def test_kaputtes_json_wirft_die_dokumentierte_ausnahme() -> None:
    client = _fake_client({})
    tool = _make_contracts_tool(_decorator(), client, AGENT_ID)

    with pytest.raises(InvalidActionError):
        tool("accept", "{nicht json")
