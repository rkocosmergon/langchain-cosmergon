# Für den Gründer — lies dies zuerst

**Stand:** 2026-04-24 ~11:00 (S147 Block 3)

Dieser Ordner `docs/drafts/langchain-cosmergon/` enthält **alle Dateien für das zukünftige Repo `rkocosmergon/langchain-cosmergon`**. Alles ist fertig, lokal getestet, CI-ready. Was noch fehlt, ist deine Entscheidung zum Rollout und ein paar Account-Aktionen, die nur du ausführen kannst.

## Was ist drin?

### Laufzeit-Code
- `src/langchain_cosmergon/__init__.py` — Public API (exportiert `cosmergon_tools`)
- `src/langchain_cosmergon/tools.py` — 4 LangChain-Tools + HTTP-Error-Translator
- `src/langchain_cosmergon/exceptions.py` — 5 typisierte Fehlerklassen mit Doc-Links
- `src/langchain_cosmergon/version.py` — `__version__ = "0.1.0"`

### Tests
- `tests/test_error_handling.py` (11) + `tests/test_tools.py` (21) = 32 Tests
- Lokal in sauberer venv mit langchain-core 0.3.84 + ruff 0.15.11 verifiziert: **alles grün**

### Docs
- `README.md` — Quickstart + 30s-Why-Pitch + Response-Times + Links
- `SECURITY.md` — Disclosure-Policy, Adresse `bot@cosmergon.com`
- `FAQ.md` — 11 Q&A für typische LangChain-User-Fragen
- `CHANGELOG.md` — Format nach Keep-a-Changelog
- `CONTRIBUTING.md` — Scope, Bug-Reporting, PR-Process, Code-Style, Philosophie
- `LICENSE` — MIT (RKO Consult UG)
- `docs/data-flow.md` — PII-Disclaimer, DSGVO-Einordnung, was-wohin-fliesst

### Beispiele
- `examples/01_profit_maximizer.py` — Minimaler Decision-Loop
- `examples/02_coordinated_agents.py` — Scout + Trader unter einem Master-Key
- `examples/03_benchmark_report.py` — 6-Dim-Performance-Report abfragen
- `examples/04_local_ollama.py` — Local LLM via Ollama (Model-Agnostik-Demo)
- `examples/README.md` — Safety-Notes, Prerequisites, CrewAI-Hint

### Packaging & CI
- `pyproject.toml` — hatchling, Python 3.10+, deps httpx + langchain-core `<0.4`
- `.gitignore`
- `.github/workflows/publish.yml` — **nur `workflow_dispatch`** (S127-Regel bindend!)
- `.github/workflows/test.yml` — Matrix 3×3 (Python 3.10/3.11/3.12 × LangChain 0.1/0.2/0.3)

## Was du tun musst (keine Prod-Deploys)

### Schritt 1 — GitHub-Repo anlegen

1. Öffne [github.com/new](https://github.com/new)
2. Name: `langchain-cosmergon`
3. Owner: `rkocosmergon`
4. Public, MIT-License-Template **NICHT** aktivieren (wir bringen unsere eigene)
5. Keine README, keine .gitignore (wir bringen unsere)
6. Repo erstellen

### Schritt 2 — PyPI Trusted Publisher konfigurieren

1. Öffne [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing) (nach Login)
2. Add a new pending publisher:
   - **PyPI Project Name:** `langchain-cosmergon`
   - **Owner:** `rkocosmergon`
   - **Repository name:** `langchain-cosmergon`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`

### Schritt 3 — Repo lokal pushen

```bash
cd ~/projekte/cos20
bash scripts/prepare-langchain-cosmergon-repo.sh
# → erstellt /tmp/langchain-cosmergon als git-initialisiertes Repo

cd /tmp/langchain-cosmergon
git remote add origin git@github.com:rkocosmergon/langchain-cosmergon.git
git push -u origin main
```

### Schritt 4 — CI durchlaufen lassen

Nach dem Push läuft die `test.yml`-Workflow automatisch (3×3 Matrix = 9 Kombinationen).
Prüfen in: `https://github.com/rkocosmergon/langchain-cosmergon/actions`
Alle 9 müssen grün sein — falls nicht, melden. (Ich rechne aber mit grün, weil lokal mit Ruff 0.15 + langchain-core 0.3 bereits verifiziert.)

### Schritt 5 — Erstes Release 0.1.0 veröffentlichen

- GitHub UI → Actions-Tab → "Publish to PyPI" → "Run workflow"
- PyPI-Trusted-Publisher-OIDC macht den Rest, keine manuellen API-Token

Nach Release: `pip install langchain-cosmergon` funktioniert weltweit.

### Schritt 6 (optional, später) — LangChain-Community-PR

Filed an [github.com/langchain-ai/langchain-community](https://github.com/langchain-ai/langchain-community) um Listing zu beantragen. Das ist der Discovery-Hebel aus der Strategie-Fortschreibung.

## Backend-seitige Änderungen

Im Feature-Branch `feat/s147-ad1-p0-prep`:

- `backend/app/core/api_metrics.py` — neue Middleware + Prometheus-Metric für Client-Type-Tracking
- `backend/app/core/trial_tier.py` — Helper für 30-Tage-Starter-Tier
- `backend/alembic/versions/0071_langchain_starter_tier_trial.py` — neue Spalten `trial_expires_at` + `trial_source`
- `backend/app/models/player.py` — Player-Model erweitert
- 32 neue Backend-Tests, Full-Suite 1901 passed ohne Regression

**Noch nicht in Prod.** Merge-Pfad: Feature-Branch → main via Fast-Forward, dann `cos-deploy`. Empfehlung: **nach** AD1-Release deployen, damit die Client-Type-Telemetrie direkt neue LangChain-Nutzung trackt.

## P0-Punkte die ich NICHT machen konnte (Gründer-Aktion)

| # | Aufgabe |
|---|---|
| P0-1 | PyPI-2FA auf `rkocosmergon`-Account verifizieren + Trusted-Publisher-Config (Schritt 2 oben) |
| P0-7 | Report #7 redaktionell kuratieren bis 27.04. mit neuer Methodology-Appendix-Section |
| P0-8 | Externen Quickstart-Test organisieren — 1 Person ausserhalb deines Kontexts |

## Pause-fertiges Material bis 12:30

Ich habe ab jetzt (11:05) nur noch kleinere Polish-Arbeiten laufen. Kein neuer Scope. Wenn du um 12:30 zurückkommst, ist alles oben bereit.

## Alles anzeigen

```bash
git -C ~/projekte/cos20 log --oneline feat/s147-ad1-p0-prep ^main | cat
git -C ~/projekte/cos20 diff --stat main..feat/s147-ad1-p0-prep | tail -3
ls -R docs/drafts/langchain-cosmergon/
```

Tracker mit Live-Status: `docs/ad1-release-tracker.md`
Panel-Protokoll: `docs/panels/panel-langchain-release-readiness-s147-2026-04-24.md`
