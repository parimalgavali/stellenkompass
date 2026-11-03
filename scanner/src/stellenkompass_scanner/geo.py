"""Decide whether a posting is in Germany and which German city it names."""

from __future__ import annotations

import re

# Display name -> spellings seen in postings (lowercase).
CITIES: dict[str, tuple[str, ...]] = {
    "Berlin": ("berlin",),
    "Hamburg": ("hamburg",),
    "Munich": ("munich", "münchen", "muenchen"),
    "Cologne": ("cologne", "köln", "koeln"),
    "Frankfurt": ("frankfurt",),
    "Stuttgart": ("stuttgart",),
    "Düsseldorf": ("düsseldorf", "dusseldorf", "duesseldorf"),
    "Leipzig": ("leipzig",),
    "Dortmund": ("dortmund",),
    "Essen": ("essen",),
    "Bremen": ("bremen",),
    "Dresden": ("dresden",),
    "Hanover": ("hanover", "hannover"),
    "Nuremberg": ("nuremberg", "nürnberg", "nuernberg"),
    "Duisburg": ("duisburg",),
    "Bochum": ("bochum",),
    "Wuppertal": ("wuppertal",),
    "Bielefeld": ("bielefeld",),
    "Bonn": ("bonn",),
    "Münster": ("münster", "muenster"),
    "Karlsruhe": ("karlsruhe",),
    "Mannheim": ("mannheim",),
    "Augsburg": ("augsburg",),
    "Wiesbaden": ("wiesbaden",),
    "Mönchengladbach": ("mönchengladbach", "moenchengladbach"),
    "Gelsenkirchen": ("gelsenkirchen",),
    "Aachen": ("aachen",),
    "Braunschweig": ("braunschweig", "brunswick"),
    "Kiel": ("kiel",),
    "Chemnitz": ("chemnitz",),
    "Halle": ("halle (saale)", "halle/saale", "halle an der saale"),
    "Magdeburg": ("magdeburg",),
    "Freiburg": ("freiburg",),
    "Krefeld": ("krefeld",),
    "Mainz": ("mainz",),
    "Lübeck": ("lübeck", "luebeck"),
    "Erfurt": ("erfurt",),
    "Rostock": ("rostock",),
    "Kassel": ("kassel",),
    "Potsdam": ("potsdam",),
    "Saarbrücken": ("saarbrücken", "saarbruecken"),
    "Paderborn": ("paderborn",),
    "Darmstadt": ("darmstadt",),
    "Regensburg": ("regensburg",),
    "Würzburg": ("würzburg", "wuerzburg"),
    "Ingolstadt": ("ingolstadt",),
    "Heidelberg": ("heidelberg",),
    "Ulm": ("ulm",),
    "Wolfsburg": ("wolfsburg",),
    "Göttingen": ("göttingen", "goettingen"),
    "Erlangen": ("erlangen",),
    "Jena": ("jena",),
    "Tübingen": ("tübingen", "tuebingen"),
    "Gütersloh": ("gütersloh", "guetersloh"),
    "Osnabrück": ("osnabrück", "osnabrueck"),
    "Oldenburg": ("oldenburg",),
    "Heilbronn": ("heilbronn",),
    "Walldorf": ("walldorf",),
    "Herzogenaurach": ("herzogenaurach",),
    "Garching": ("garching",),
    "Unterföhring": ("unterföhring",),
}

STATES = (
    "baden-württemberg", "baden-wurttemberg", "bavaria", "bayern", "brandenburg",
    "hesse", "hessen", "lower saxony", "niedersachsen", "mecklenburg", "north rhine-westphalia",
    "nordrhein-westfalen", "nrw", "rhineland-palatinate", "rheinland-pfalz", "saarland",
    "saxony", "sachsen", "schleswig-holstein", "thuringia", "thüringen",
)  # fmt: skip

STATE_CODES = {
    "bw", "by", "be", "bb", "hb", "hh", "he", "mv", "ni", "nw", "rp", "sl", "sn", "st", "sh", "th",
}  # fmt: skip

_COUNTRY = ("germany", "deutschland", "dach")
_REMOTE_SCOPE = (
    "europe", "emea", "eu ", "(eu)", "dach", "germany", "deutschland", "worldwide", "anywhere",
)  # fmt: skip
_REMOTE_WORDS = ("remote", "home office", "homeoffice", "fully distributed")


def _has_word(text: str, word: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", text) is not None


def city_of(*texts: str) -> str:
    """First German city named in the given location texts, as a display name."""
    for text in texts:
        low = (text or "").lower()
        for name, spellings in CITIES.items():
            if any(_has_word(low, s) for s in spellings):
                return name
    return ""


def mentions_germany(text: str) -> bool:
    low = (text or "").lower()
    if any(_has_word(low, w) for w in _COUNTRY) or any(_has_word(low, s) for s in STATES):
        return True
    return city_of(low) != ""


def is_remote(text: str) -> bool:
    low = (text or "").lower()
    return any(w in low for w in _REMOTE_WORDS)


def remote_open_to_germany(text: str) -> bool:
    """Remote role whose location text includes Germany, the EU/EMEA/DACH region or 'anywhere'."""
    low = (text or "").lower() + " "
    return is_remote(low) and any(scope in low for scope in _REMOTE_SCOPE)


def in_germany(locations: list[str], country_codes: list[str] | None = None) -> bool:
    codes = {c.lower() for c in (country_codes or []) if c}
    if codes & {"de", "deu", "germany", "deutschland"}:
        return True
    joined = " | ".join(x for x in locations if x)
    return mentions_germany(joined) or remote_open_to_germany(joined)
