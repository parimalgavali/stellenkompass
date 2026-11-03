"""One module per job source.

Company boards have `fetch(fetcher, board)` and `parse(raw, board)`; aggregators have
`fetch(fetcher, options)` and `parse(raw)`, with options from their section in companies.yaml.
"""

from . import (
    arbeitnow,
    ashby,
    bundesagentur,
    dvinci,
    greenhouse,
    lever,
    personio,
    recruitee,
    smartrecruiters,
    teamtailor,
    workday,
)

PER_COMPANY = {
    "greenhouse": greenhouse,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
    "lever": lever,
    "personio": personio,
    "recruitee": recruitee,
    "teamtailor": teamtailor,
    "dvinci": dvinci,
    "workday": workday,
}

AGGREGATORS = {
    "arbeitnow": arbeitnow,
    "bundesagentur": bundesagentur,
}
