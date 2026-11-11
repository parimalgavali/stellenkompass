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
    join,
    lever,
    personio,
    recruitee,
    smartrecruiters,
    softgarden,
    successfactors,
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
    "successfactors": successfactors,
    "softgarden": softgarden,
    "join": join,
}

AGGREGATORS = {
    "arbeitnow": arbeitnow,
    "bundesagentur": bundesagentur,
}
