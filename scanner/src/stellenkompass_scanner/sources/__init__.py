"""One module per job source. Each has `fetch(fetcher, board)` and `parse(raw, board)`."""

from . import arbeitnow, ashby, greenhouse, lever, personio, smartrecruiters

PER_COMPANY = {
    "greenhouse": greenhouse,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
    "lever": lever,
    "personio": personio,
}

AGGREGATORS = {
    "arbeitnow": arbeitnow,
}
