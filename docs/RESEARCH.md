# Research: how the inspiration sites work

Collected on 2026-11-03 from public pages and the public JavaScript each site sends to the browser. We did not log in to any paid area.

## Arbeit49 (arbeit49.zerozerofournine.com)

Paid job-search app for Germany by "Zero Zero Four Nine (0049)".

**Tech (seen in public JS):** Next.js app, Firebase (auth + data), Google Cloud Functions in `europe-west3`, Stripe for billing. Everything except the sign-in screen and legal pages needs an account.

**Features (from UI text in the app bundle):**
- **Job scan:** reads "the Bundesagentur für Arbeit, 200,000+ company career sites and nine applicant-tracking platforms". Daily scan on paid plans, weekly on the free plan, plus an on-demand scan and a market-wide "Discover" scan.
- **Scan profile:** keywords and followed companies (free plan: 10 keywords, 5 companies). Preferences for Germany location, start date and salary.
- **Matches:** list of roles that fit the scan profile; roles that are no longer listed get archived.
- **Application tracker:** stages Saved, Applied, Interview, Offer, Rejected. Dates for applied and interview. Nudges such as "Follow up after the interview", "Still interested? Apply or close", "Close? No answer since…", "Thank-you note".
- **Today view:** greeting, "Nothing is due today", what to do next.
- **AI apply kits:** import CV once; per role it prepares "Why this company and role", standard and role/technical questions.
- **Chrome extension:** save jobs from any site in one click.
- **Email job alerts.**
- **Paid extras:** community (Family49), monthly 1:1 call, human CV review. Not relevant for us.

**What we take:** scan profile (keywords + followed companies), matches, tracker stages and nudges, Today view, later the apply kit and extension.
**What we drop:** login, plans, payments, limits, community.

## Arbeitnow (arbeitnow.com)

Free job board for Germany with a focus on English-speaking roles.

- Public JSON API: `https://www.arbeitnow.com/api/job-board-api` (paginated; fields include title, company, location, remote, tags, job types, created date, description HTML, url).
- Filter ideas: English-speaking, visa sponsorship, relocation package, salary shown, 4-day week, by city and category.
- Useful extras: tax calculator, Germany job market insights.

**What we take:** use the API as a source; English-speaking / visa / relocation filters.

## workingstudentjobs.de

Job board for working student and internship roles in Germany (behind Cloudflare bot protection, so we don't read it automatically).

- Language switch: English / German / All.
- Filters: location, field, job type (working student, internship), working mode (on-site, hybrid, remote).
- Cards show company logo, posted "x hours ago", city, working mode, field and skill tags.
- "Updated hourly", "Quality reviewed", saved jobs, job alerts, salary guide.

**What we take:** the language switch, job type and working mode filters, card layout with skill tags.

## Astra (useastra.in)

Indian job + interview-prep platform.

- "Resume to jobs": upload CV, get roles with a "% fit" score and an ATS score with fixes.
- Saved → Applied → Interview → Offer tracker.
- Interview prep next to each job.

**What we take (v2):** CV-based fit score, prep next to each tracked job.

## Job sources we checked (2026-11-03)

| Source | Public endpoint | Works from the VM? |
| --- | --- | --- |
| Arbeitnow | `arbeitnow.com/api/job-board-api` | Yes |
| Greenhouse | `boards-api.greenhouse.io/v1/boards/{company}/jobs` | Yes |
| Ashby | `api.ashbyhq.com/posting-api/job-board/{company}` | Yes |
| SmartRecruiters | `api.smartrecruiters.com/v1/companies/{company}/postings` | Yes |
| Lever | `api.lever.co/v0/postings/{company}?mode=json` | Yes |
| Personio | `{company}.jobs.personio.de/xml` | Yes |
| Bundesagentur für Arbeit | `rest.arbeitsagentur.de/jobboerse/jobsuche-service/...` | No (HTTP 403 from the VM). Retry from GitHub Actions later. |
