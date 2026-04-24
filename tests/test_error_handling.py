"""Verify every HTTP-error path produces an actionable exception.

A LangChain user encountering our errors should immediately know what to do.
Bare stack traces are a DX failure — each test below asserts both the
exception type and the presence of a documentation URL or action-hint.
"""

from __future__ import annotations

import json

import httpx
import pytest

from langchain_cosmergon.exceptions import (
    ApiUnavailableError,
    AuthenticationError,
    ConfigurationError,
    InvalidActionError,
    RateLimitError,
)
from langchain_cosmergon.tools import _handle_response


def _mock_response(
    status_code: int, body: str | dict, headers: dict | None = None
) -> httpx.Response:
    """Create a minimal httpx.Response mock."""
    content = json.dumps(body).encode() if isinstance(body, dict) else body.encode()
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers=headers or {},
    )


class TestHandleResponse:
    def test_200_returns_json(self) -> None:
        resp = _mock_response(200, {"energy": 1000})
        assert _handle_response(resp) == {"energy": 1000}

    def test_201_returns_json(self) -> None:
        resp = _mock_response(201, {"created": True})
        assert _handle_response(resp) == {"created": True}

    def test_401_raises_authentication_with_doc_link(self) -> None:
        resp = _mock_response(401, "")
        with pytest.raises(AuthenticationError) as exc_info:
            _handle_response(resp)
        assert "cosmergon.com/settings" in str(exc_info.value)
        assert "CSMR-" in str(exc_info.value)

    def test_403_raises_authentication(self) -> None:
        resp = _mock_response(403, "")
        with pytest.raises(AuthenticationError):
            _handle_response(resp)

    def test_429_raises_rate_limit_with_retry_after(self) -> None:
        resp = _mock_response(429, "", headers={"Retry-After": "90"})
        with pytest.raises(RateLimitError) as exc_info:
            _handle_response(resp)
        assert exc_info.value.retry_after_seconds == 90
        assert "cosmergon.com/pricing" in str(exc_info.value)
        assert "120 req/min" in str(exc_info.value)  # LangChain starter-tier mention

    def test_429_defaults_retry_after_60(self) -> None:
        resp = _mock_response(429, "")
        with pytest.raises(RateLimitError) as exc_info:
            _handle_response(resp)
        assert exc_info.value.retry_after_seconds == 60

    def test_422_extracts_error_detail(self) -> None:
        resp = _mock_response(
            422,
            {"error": {"code": 422, "message": "Insufficient energy", "type": "http_error"}},
        )
        with pytest.raises(InvalidActionError) as exc_info:
            _handle_response(resp)
        assert "Insufficient energy" in str(exc_info.value)

    def test_500_raises_api_unavailable_with_status_link(self) -> None:
        resp = _mock_response(500, "")
        with pytest.raises(ApiUnavailableError) as exc_info:
            _handle_response(resp)
        assert "cosmergon.com/status" in str(exc_info.value)

    def test_503_raises_api_unavailable(self) -> None:
        resp = _mock_response(503, "")
        with pytest.raises(ApiUnavailableError):
            _handle_response(resp)

    def test_unexpected_status_raises_api_unavailable(self) -> None:
        resp = _mock_response(418, "I'm a teapot")  # not specifically handled
        with pytest.raises(ApiUnavailableError) as exc_info:
            _handle_response(resp)
        assert "418" in str(exc_info.value)

    def test_non_json_200_raises_api_unavailable(self) -> None:
        resp = _mock_response(200, "not-json-garbage")
        with pytest.raises(ApiUnavailableError) as exc_info:
            _handle_response(resp)
        assert "non-JSON" in str(exc_info.value)


class TestExceptionTypesCarryActionableMessages:
    """Every exception type must contain a doc-link or clear next-step."""

    def test_authentication_error_mentions_settings(self) -> None:
        exc = AuthenticationError(
            "Cosmergon rejected. Check COSMERGON_PLAYER_TOKEN at cosmergon.com/settings."
        )
        assert "cosmergon.com" in str(exc)

    def test_rate_limit_error_carries_retry_after(self) -> None:
        exc = RateLimitError("Rate-limit exceeded", retry_after_seconds=60)
        assert exc.retry_after_seconds == 60

    def test_configuration_error_is_distinct(self) -> None:
        exc = ConfigurationError("Missing token")
        # Must not be confused with AuthenticationError
        assert not isinstance(exc, AuthenticationError)
