# Firecrawl Alexandria (job providers)

Checked 2026-11-03 from the public pages: [alexandria.firecrawl.dev/categories/jobs](https://alexandria.firecrawl.dev/categories/jobs), [docs](https://docs.firecrawl.dev/features/alexandria). The app link (`firecrawl.dev/app/...`) needs a Firecrawl login, so it wasn't opened.

## What it is
- A paid data API for AI agents, not a job site. One Firecrawl key gives access to many "providers" (jobs, companies, finance, …).
- Find a tool with `POST /v2/search` (`sources: ["alexandria"]`, free), run it with `POST /v2/scrape` and `{"alexandria": {"provider", "capability", "options"}}` (costs credits). Also available as SDK, CLI and MCP.

## Job providers (15)
| Provider | What it gives | Us |
| --- | --- | --- |
| Greenhouse, Ashby, SmartRecruiters, Workday, SAP SuccessFactors | One employer's board: list, search, posting detail | Already read directly, free |
| JOIN (`join-com`) | One employer: profile, jobs by category/city, ad detail, categories; no cross-company search | Added (D26) |
| iCIMS | One employer portal: search, posting detail | Not yet; mostly US employers |
| TheirStack, BlitzAPI, Crustdata, Sumble | Resold job/company data, priced per result (TheirStack: 10 credits per job) | No: paid; TheirStack says ~40% of its jobs come from Indeed and ~19% from LinkedIn |
| Glassdoor (US), Built In (US tech) | Job search | No: US only |
| JobLeads | First 10 results per search; later pages use a private API | No: private API |
| Y Combinator, Wayfair | Startup directory; one employer | No |

## What we take
- JOIN as a source, read from the public company pages robots.txt allows.
- The idea of one normalized job shape across employer boards, which `Job` already is.
- Not taken: paying per call, resold LinkedIn/Indeed data, private APIs.
