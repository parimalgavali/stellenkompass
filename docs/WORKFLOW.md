# How we work

The loop for every piece of work:

1. **Issue** — one GitHub Issue per user story (story + acceptance criteria), assigned to `parimalgavali`.
2. **Branch** — from latest `main`: `devin/<timestamp>-<slug>`. No stacked PRs.
3. **Build** — best practices: small focused changes, tests for new logic, lint/format clean.
4. **Check locally**
   - Scanner: `cd scanner && uv run ruff check . && uv run ruff format --check . && uv run pytest -q`
   - Web: `cd web && npx oxlint && npm test && npm run build`
5. **Docs** — update [CHECKLIST.md](CHECKLIST.md), and [DECISIONS.md](DECISIONS.md) for any new decision.
6. **PR** — short description (what + why + `Closes #N`), assigned to `parimalgavali`.
7. **Merge** — once CI is green, merge it. Fix merge conflicts directly.

## Docs map
- [PLANS.md](PLANS.md) — architecture and phases
- [CHECKLIST.md](CHECKLIST.md) — progress
- [DECISIONS.md](DECISIONS.md) — decision log
- [RESEARCH.md](RESEARCH.md) — what we learned from Arbeit49, Arbeitnow, Astra, workingstudentjobs.de
- [DATA_SOURCES.md](DATA_SOURCES.md) — job sources and the common job format
