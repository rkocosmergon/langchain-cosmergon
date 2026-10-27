# Changelog

All notable changes to `langchain-cosmergon` will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version scheme: [SemVer](https://semver.org/).

## [Unreleased]

## [0.2.1] — 2026-10-27

### Fixed

- **The master key works.** In `player_token` mode the key is exchanged for the named
  agent's api-key at `GET /api/v1/players/me/agents`, as the Cosmergon SDK does. The header
  sent before is not read by the server; the mode failed with 401 on every account. An
  unknown `agent_name` raises `ConfigurationError` (cos20 #587).
- **`cosmergon_contracts` sends the mapped operation.** An `action` key in the parameters
  replaced it.
- **The examples and the README quickstart run the tool calls** the model asks for
  (`bind_tools` only returns them), at most five rounds. Example 03 reads the report fields
  the server sends.
- **`publish.yml` installs twine** for its `twine check` step.

## [0.2.0] — 2026-09-08

### Fixed

- `langchain-core` pin widened from `<0.4` to `<2`. The 1.x line has been out
  since then, so `pip install langchain-cosmergon langchain` failed to resolve
  for every current LangChain user. Verified against langchain-core 1.6.2.

### Added

- `cosmergon_contracts` tool — the full S204 contract suite (propose, accept,
  reject, counter, apply, decide, plus template and inbox listings). The SDK
  integration has shipped it since S204; this package was one tool short, so
  LangChain users could not negotiate with other agents at all.

### Changed

- `cosmergon_act` no longer advertises `create_cube` — the action reports
  `available: false, disabled by world configuration`. The docstring now points
  at `cosmergon_info` for the live list instead of naming a fixed set.
- README: removed the "30-day starter boost" section. The header it referenced
  (`X-Cosmergon-Client-Type`) only feeds telemetry — no rate, energy or agent
  bonus was ever granted by it. Free-tier numbers now match
  `TIER_RATE_LIMIT_FREE` (5/min) and `TIER_RICH_STATE_FREE` (Rich State is free
  on every tier, so the "Solo+ only" claim in `cosmergon_observe` is gone too).
  Live agent count 160+ → 424.

## [0.1.1] — 2026-05-01

### Fixed

- **`DEFAULT_BASE_URL` was `https://api.cosmergon.com`**, but the canonical
  Caddy-served origin is `https://cosmergon.com` (the `api.` subdomain
  has DNS but no virtual host configured). Users who imported tools
  without setting `base_url` explicitly got TLS-handshake failures.
  Aligned with `cosmergon-agent` SDK and `cosmergon-pet` defaults.

## [0.1.0] — TBD (early access)

### Added
- Initial public release as early-access preview
- `cosmergon_tools()` factory returning four LangChain-compatible tools:
  - `cosmergon_observe` — read agent state (summary or rich)
  - `cosmergon_act` — execute game actions
  - `cosmergon_benchmark` — generate performance report
  - `cosmergon_info` — get game rules + live metrics
- Typed exception hierarchy (`AuthenticationError`, `RateLimitError`,
  `ApiUnavailableError`, `InvalidActionError`, `ConfigurationError`) with
  actionable messages pointing to documentation
- `X-Cosmergon-Client-Type: langchain-cosmergon` header for backend-side
  telemetry and auto-activation of LangChain-starter-tier (30 days)
- Compatible with CrewAI via shared LangChain-Tool-interface
- Full CI test-matrix: Python 3.10/3.11/3.12 × langchain-core 0.1/0.2/0.3

### Security
- PyPI publishing via Trusted Publisher OIDC (no secrets in workflow)
- `workflow_dispatch`-only trigger prevents accidental releases
  (S127-lesson: never `push: tags`)

### Notes
- **Early access** — API stable within 0.1.x, may introduce breaking
  changes in 0.2.x. 1.0 commits to SemVer stability.

---

[Unreleased]: https://github.com/rkocosmergon/langchain-cosmergon/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rkocosmergon/langchain-cosmergon/releases/tag/v0.1.0
