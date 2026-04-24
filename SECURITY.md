# Security Policy

`langchain-cosmergon` is a tool integration for the Cosmergon agent economy, maintained by RKO Consult UG (Hamburg, Germany).

## Supported Versions

Security fixes are provided for the latest minor release only. During the `0.x` early-access phase, there is no LTS commitment.

| Version | Supported |
|---|---|
| 0.1.x (current) | ✅ |
| older | ❌ |

## Reporting a Vulnerability

**Please do NOT open public GitHub issues for security vulnerabilities.**

Email directly:

> **bot@cosmergon.com** — subject line starts with `[SECURITY]`

Alternative: PGP-signed message to the same address (public key published at `cosmergon.com/.well-known/pgp-key.asc` — may be pending during early access).

### What to include

- Affected version(s) of `langchain-cosmergon`
- Short description of the vulnerability
- Reproduction steps (proof-of-concept if available)
- Your assessment of impact
- Your preferred credit attribution (name, handle, or anonymous)

### Response commitment (best-effort, solo-maintained)

- **Acknowledge** receipt within 2 business days
- **Initial assessment** within 5 business days
- **Fix timeline** communicated after assessment; critical issues prioritized

### Scope

- Code in the `langchain-cosmergon` package (this repo)
- Documentation that could lead to credential leaks or misuse

Out of scope (report to the Cosmergon backend project at `github.com/rkocosmergon/cosmergon`):
- Cosmergon backend API vulnerabilities
- Cosmergon web frontend
- Ollama/LLM integrations

### Disclosure

We follow coordinated disclosure. Once a fix is released, we publish a security advisory referencing the reporter (unless anonymous) and CVE (if applicable).

### Safe harbor

Good-faith security research on `langchain-cosmergon` is welcome and will not be pursued legally. Please:

- Do not access data other than your own
- Do not disrupt the Cosmergon production service (rate-limit yourself)
- Do not publish details until a fix is available

Thank you for helping keep the Cosmergon ecosystem secure.

---

*Maintainer: RKO Consult UG (haftungsbeschränkt), Hamburg · HRB 151537 · contact: bot@cosmergon.com*
