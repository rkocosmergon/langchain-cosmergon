# Contributing to langchain-cosmergon

Thanks for considering a contribution! This is an early-access package maintained by a solo developer, so please read the guidelines below before opening issues or PRs.

## Scope

**In scope for this package:**
- Bug fixes in the tool implementations
- Compatibility fixes for new LangChain-core releases
- Error-message improvements (we want actionable messages, not stack traces)
- New examples for common use cases
- Documentation clarifications

**Out of scope (belongs in other repos):**
- Cosmergon backend API changes → [github.com/rkocosmergon/cosmergon](https://github.com/rkocosmergon/cosmergon) (private, opt-in collaboration)
- Cosmergon core SDK features → [github.com/rkocosmergon/cosmergon-agent](https://github.com/rkocosmergon/cosmergon-agent)
- Game rules, economy mechanics → [cosmergon.com/reports](https://cosmergon.com/reports) + Cosmergon-College (future)

## How to report a bug

1. Check existing issues first: [github.com/rkocosmergon/langchain-cosmergon/issues](https://github.com/rkocosmergon/langchain-cosmergon/issues)
2. Open a new issue with:
   - `langchain-cosmergon` version (`pip show langchain-cosmergon`)
   - `langchain-core` version
   - Python version
   - Minimal reproduction (5–10 lines of code)
   - Full error message
3. Label: `bug`

**Do not include your `COSMERGON_PLAYER_TOKEN` or any API key in the reproduction.** Redact before posting.

## How to ask a question

Use [GitHub Discussions](https://github.com/rkocosmergon/langchain-cosmergon/discussions) (no live chat / Discord during early access). Best-effort response within a week.

## How to propose a feature

1. Check the [AD1 Release-Tracker](https://github.com/rkocosmergon/cosmergon/blob/main/docs/ad1-release-tracker.md) for planned post-release work
2. Open a GitHub Discussion in "Ideas" category first — don't submit a PR without prior alignment
3. Note: Feature requests are reviewed quarterly during early access

## How to submit a PR

1. **Fork** and create a branch: `fix/short-description` or `feat/short-description`
2. **Install dev deps:** `pip install -e ".[dev]"`
3. **Ruff lint + format:** `ruff check . && ruff format .`
4. **Run tests:** `pytest -v`
5. **Open PR against `main`** with:
   - Clear title and description
   - Link to the issue being fixed (if any)
   - Test coverage for any new code path

**We run CI on Python 3.10/3.11/3.12 × langchain-core 0.1/0.2/0.3.** If your change breaks any combination, the PR will be blocked until fixed.

## Security issues

**Do NOT open public issues for security problems.** Follow the disclosure process in [SECURITY.md](./SECURITY.md).

## Code style

- **Ruff** is the source of truth. No style debates — ruff decides.
- **Line length 100.**
- **Type hints** everywhere public.
- **Docstrings** on public functions (Google or NumPy style accepted).
- **Error messages** must include a doc-link or clear action-hint. No bare stack traces.

## Philosophy

This package exists to make Cosmergon findable in the LangChain ecosystem. Its value is in being *reliable*, not in being feature-rich. We err on the side of:

- **Stable API** over new features
- **Clear errors** over clever retries
- **Explicit config** over magic defaults
- **MIT license** for ecosystem compatibility

Thanks for helping make it better.

---

*Package maintained by RKO Consult UG (haftungsbeschränkt), Hamburg · HRB 151537*
