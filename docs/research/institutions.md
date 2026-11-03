# Universities and research institutes: pilot inventory

What this is: the pilot institutions from the review (work item 8), checked one by one on 2026-11-03.
It is **not** a list of all German universities. The full inventory (from
[Hochschulkompass](https://www.hochschulkompass.de/)) is still open, see `docs/CHECKLIST.md` Phase 11.

Status:
- `enabled`: a collector runs in the daily scan.
- `pending`: no usable machine-readable route found yet; check again or write a narrow parser.
- `blocked`: a route exists, but robots.txt or the site refuses our client. We don't work around it.

Order of preference for a collector: existing ATS adapter → documented feed → JobPosting JSON-LD →
narrow HTML parser. None of the pilot pages had JobPosting JSON-LD.

| Institution | Type | Jobs page | System | Route checked | Status | Notes |
|---|---|---|---|---|---|---|
| KIT | University + research | [kit.edu](https://www.kit.edu/karriere/stellenangebote.php) | d.vinci | `jobs.pse.kit.edu/jobPublication/list.json` | enabled | 73 ads → 39 roles: 21 Ausbildung/dual-study ads skipped, 13 openings published in German and English kept once. Includes SCC (IT centre) and PhD/postdoc roles. |
| TUM | University | [tum.de](https://www.tum.de/ueber-die-tum/karriere-und-jobs/stellenangebote) | Own portal (portal.mytum.de) | `portal.mytum.de/jobs/asRss` | blocked | robots.txt: `Disallow: /`. The RSS is also not well-formed XML. |
| Fraunhofer | Research network | [jobs.fraunhofer.de](https://jobs.fraunhofer.de/) | SAP SuccessFactors | `/tile-search-results/` (allowed; `/services/` is disallowed) | enabled | About 700 roles in Germany via the `successfactors` adapter (D20). Some tiles have no city. |
| DLR | Research | [jobs.dlr.de](https://jobs.dlr.de/) | SAP SuccessFactors | `/tile-search-results/` | blocked | The allowed tile route returns no roles; the JSON search is under the disallowed `/services/`. |
| Max Planck Society | Research network | [mpg.de/stellenboerse](https://www.mpg.de/stellenboerse) | References b-ite | none found | pending | Institutes also post on their own sites. |
| Helmholtz | Research network | [helmholtz.de/karriere](https://www.helmholtz.de/karriere/) | none (links to centres) | none | pending | Check each centre (FZ Jülich, DESY, KIT, HZB, …). |
| FZ Jülich | Helmholtz centre | [fz-juelich.de](https://www.fz-juelich.de/de/karriere/stellenangebote) | not identified | none | pending | |
| DESY | Helmholtz centre | [desy.de](https://www.desy.de/karriere/stellenangebote/index_ger.html) | not identified | none | pending | Timed out from the dev VM. |
| DFKI | Research | [dfki.de/web/karriere](https://www.dfki.de/web/karriere) | not identified | none | blocked | HTTP 403 to our client. |
| RWTH Aachen | University | not found yet | not identified | none | pending | The old `go/id/rec` link returns 404. |
| Uni Bonn | University | [uni-bonn.de](https://www.uni-bonn.de/de/universitaet/arbeiten-an-der-uni/stellenangebote) | Plone CMS pages | HTML per category (incl. IT/Technik, students) | pending | No JSON-LD. A narrow HTML parser is possible. |
| Uni Hamburg | University | [uni-hamburg.de](https://www.uni-hamburg.de/stellenangebote.html) | not identified | none | pending | Timed out from the dev VM. |

Coverage: 1 of 12 pilot institutions enabled.

## Adding a d.vinci institution
1. On the jobs page, look for `dvinci` / `jobWidgetLoader` in the page source; the widget's host is the board.
2. Check `https://<host>/robots.txt` and `https://<host>/jobPublication/list.json`.
3. Add `- { board: <host>, name: <Institution> }` under `dvinci:` in `scanner/companies.yaml`, and a row here.
