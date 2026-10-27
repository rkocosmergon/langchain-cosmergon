"""Guard cos20 #587: the contracts tool sends the mapped action, not an "action" key in params."""

from __future__ import annotations

import json

import httpx

from langchain_cosmergon.tools import _make_contracts_tool


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
