# Changelog

All notable changes to `langchain-cosmergon` will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version scheme: [SemVer](https://semver.org/).

## [Unreleased]

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
