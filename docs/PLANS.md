# Plan

## Goal

One place to find open roles in Germany that fit me (and my friends), and to keep track of every application, without logins, payments or limits.

Inspired by Arbeit49, Arbeitnow, workingstudentjobs.de and Astra (see [RESEARCH.md](RESEARCH.md)). We rebuild the ideas in our own code with our own data from public sources. We do not copy their code, data, name or design.

## How we work

1. Every piece of work is a GitHub Issue written as a user story with acceptance criteria.
2. One feature branch per issue, branched from `main`. The PR targets `main` and says `Closes #N`.
3. CI must pass (lint + tests) before merge.
4. After each PR: tick the box in [CHECKLIST.md](CHECKLIST.md), and add a note to [DECISIONS.md](DECISIONS.md) when we chose between options.

## Architecture (v1)

```
GitHub Actions (daily cron)
   └─ scanner/ (Python)  ── reads public job sources ──►  data/jobs.json
                                                          │
web/ (React + Vite, static) ◄────────── reads ────────────┘
   ├─ Jobs list + filters
   ├─ Tracker (Saved → Applied → Interview → Offer / Rejected)
   └─ Today (what needs doing)
          └─ all personal data in the browser (localStorage), export/import as JSON
Hosted on GitHub Pages.
```

- No backend server and no database in v1. The scan output is a static JSON file.
- Personal data (tracker, notes, keywords, followed companies) never leaves the browser.

## Phases

### Phase 1: Foundation and scanner
- Repo, docs, CI.
- Python scanner with one adapter per source. All roles go into one common format (see [DATA_SOURCES.md](DATA_SOURCES.md)).
- Keep only roles in Germany (plus remote roles open to Germany).
- Detect language of the posting (English or German) and job type (full-time, working student, internship).
- Remove duplicates across sources.

### Phase 2: Web app v1
- Jobs list with search and filters: language, city, job type, remote, source, posted date.
- "My profile" in the browser: keywords and followed companies. Matching roles are highlighted and can be shown alone.
- Tracker with stages and dates (applied, interview), notes, and a link back to the posting.
- Today view: follow-ups due, interviews coming, new matches since last visit.
- Export / import of personal data as a JSON file.

### Phase 3: Daily automation and hosting
- GitHub Actions workflow that runs the scan every day, commits `jobs.json`, and deploys the site to GitHub Pages.
- Scan health: count per source, errors, last run time, shown in the app footer.

### Phase 4: Better matching (v2)
- CV upload in the browser and a simple "fit" score per role (skills overlap), computed locally.
- More sources (more company boards, Bundesagentur für Arbeit if reachable).
- Skill tags per role.

### Phase 5: AI help (v2, optional)
- "Apply kit" per role: why this company/role, likely questions, CV tailoring hints.
- Needs an LLM key. Runs only when the user asks, with their own key, never in the daily scan.

### Later ideas
- Email or Telegram alerts for new matches.
- Browser extension to save a job from any site into the tracker.
- Visa-sponsorship and salary hints where the posting states them.

## Out of scope
- Login, accounts, payments, plan limits.
- Scraping sites that forbid it, or anything behind a login or paywall.
