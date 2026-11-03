"""One module per job source.

Company boards have `fetch(fetcher, board)` and `parse(raw, board)`; aggregators have
`fetch(fetcher, options)` and `parse(raw)`, with options from their section in companies.yaml.
"""

from . import arbeitnow, ashby, bundesagentur, greenhouse, lever, personio, smartrecruiters

PER_COMPANY = {
    "greenhouse": greenhouse,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
    "lever": lever,
    "personio": personio,
}

AGGREGATORS = {
    "arbeitnow": arbeitnow,
    "bundesagentur": bundesagentur,
}
