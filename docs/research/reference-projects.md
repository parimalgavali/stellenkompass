# Reference projects review (2026-11-03)

Reviewed: [heynish/absolventen-tech-jobs-dach](https://github.com/heynish/absolventen-tech-jobs-dach)
(and its upstream `heynish/werkstudent-praktikum-jobs`), [career-ops](https://github.com/career-ops-hq/career-ops)
and its [docs](https://career-ops.org/docs). We take ideas, not code.

## What they are
- **absolventen-tech-jobs-dach**: a README table of ~70 junior/new-grad tech roles in DACH, rebuilt daily by
  GitHub Actions from the upstream list (1,803 roles from public ATS APIs + Arbeitsagentur + Adzuna).
  The upstream filter is just a regex over titles; every apply link goes through an affiliate redirect.
- **career-ops**: a local, AI-CLI-driven job search system (MIT). Zero-token scanners for ~120 ATSs and
  boards, then an LLM scores each role, tailors a CV PDF and tracks applications in local files.

## Worth adopting (ordered by value for us)
1. **Workday adapter**: public CXS endpoint `POST https://<tenant>.<wdN>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs`,
   paged. Used by Accenture, Philips, Hitachi, Roche, DB, Nvidia, … (career-ops `providers/workday.mjs`).
2. **SAP SuccessFactors (RMK) adapter**: `GET {origin}/tile-search-results/?startrow=N` on branded career
   sites (ZF, Schaeffler, SAP, Hensoldt, …). Check robots.txt per site: it may also unblock Fraunhofer/DLR,
   whose `/services/` RSS is disallowed (see institutions.md).
3. **softgarden** (`{tenant}.softgarden.io/{lang}/widgets/jobs`) and **join.com**: common with German SMEs.
4. **More boards from the upstream list**: 110 ATS boards with DACH roles are not in our `companies.yaml`
   (e.g. Drees & Sommer, Sopra Steria, Eurofins, Roland Berger, Brainlab, Doctolib, Upvest, Sereact, Oviva, FINN).
   Each must be re-checked for German roles before adding.
5. **Entry-level / seniority** label (Junior, Graduate/Trainee, Senior, Lead) and filter, from the title.
6. **Years of experience** read from the job text ("3+ Jahre Berufserfahrung") as a chip, rules only
   (career-ops `jd-years.mjs`). Nothing is dropped.
7. **Saved role no longer listed**: the tracker flags saved roles that are missing from the latest scan
   (our scan is a full snapshot, so absence is a cheap liveness signal; career-ops checks per ATS API).
8. **Application deadline** where a source gives one (d.vinci `endDate`): "closes in N days" on the card
   and in Today (career-ops `closing-soon.mjs`).

## Not adopting
- LLM scoring, CV PDF tailoring, auto-filled applications: out of scope (no keys, no automation; D10).
- Playwright scraping of stateful portals (Interamt): conflicts with "public APIs and feeds only".
- Affiliate apply links, README-as-site.
