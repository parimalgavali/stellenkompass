# Web app

React + Vite + TypeScript. It reads `data/jobs.json` from the scanner. There is no backend
and no login: each person's profile and tracker are saved in their own browser
(`localStorage`). Use Profile → Backup to export or import them.

## Run

```bash
cd web
npm install
npm run dev        # http://localhost:5173 (serves ../data/*.json at /data)
npm test           # vitest
npx oxlint         # lint
npm run build      # dist/, with ../data/*.json copied to dist/data
```

If `../data/jobs.json` is missing, run the scanner first (see `scanner/README.md`).

## Pages

| Page | What it does |
| --- | --- |
| Jobs | Search title, company and tags. Filter by language, city, type, posted date, source, remote and "My matches". |
| Today | Follow-ups (applied 7+ days ago with no update), interviews in the next 7 days, thank-you notes, saved roles older than 5 days, and new matches since your last visit. |
| Tracker | Saved → Applied → Interview → Offer / Rejected / Closed, with dates and notes. Roles stay here after they leave the scan. |
| Profile | Keywords, followed companies and your skills (load a CV: read in the browser, only skills are kept), plus JSON export and import (merge or replace). |
