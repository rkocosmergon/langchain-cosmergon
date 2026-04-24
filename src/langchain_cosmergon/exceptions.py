"""Typed exceptions for langchain-cosmergon.

Thin wrapper over httpx errors — every exception carries an actionable
message for LangChain users. No stack-traces leak to end users; messages
explain what went wrong and what to do next.
"""

from __future__ import annotations


class CosmergonError(Exception):
    """Base class for all langchain-cosmergon errors."""


class AuthenticationError(CosmergonError):
    """Your player token or API key is invalid / expired / misformatted.

    Typical fixes:
    - Check `COSMERGON_PLAYER_TOKEN` env var (must start with `CSMR-`)
    - Regenerate at https://cosmergon.com/settings (Solo+ feature)
    - If using api_key directly: format is `AGENT-<id>:<secret>`
    """


class RateLimitError(CosmergonError):
    """Cosmergon API rate-limit exceeded.

    Free tier: 60 requests/minute per IP. LangChain starter-tier: 120/min.
    Wait 60 seconds or upgrade at https://cosmergon.com/pricing.

    The `retry_after_seconds` attribute carries the server's hint.
    """

    def __init__(self, message: str, retry_after_seconds: int = 60) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ApiUnavailableError(CosmergonError):
    """Cosmergon API returned 5xx or connection failed.

    Check https://cosmergon.com/status for live status.
    If status page shows green, retry in 30–60 seconds. If persistent,
    report at https://github.com/rkocosmergon/langchain-cosmergon/issues.
    """


class InvalidActionError(CosmergonError):
    """The action you tried isn't valid for your current game state.

    Examples:
    - Insufficient energy for the operation
    - Field already exists at target coordinates
    - Action requires Solo+ tier

    The API's explanation is preserved in the message.
    """


class ConfigurationError(CosmergonError):
    """Your configuration is missing required fields.

    Typical fixes:
    - Pass `player_token=...` or `api_key=...` explicitly
    - Or set `COSMERGON_PLAYER_TOKEN` / `COSMERGON_API_KEY` env var
    """
