import pytest

from stellenkompass_scanner.geo import city_of, in_germany, is_remote


@pytest.mark.parametrize(
    "locations, codes, expected",
    [
        (["Berlin"], None, True),
        (["München, Bayern"], None, True),
        (["Charlottenburg, Berlin, Germany"], None, True),
        (["Paris"], None, False),
        (["New York", "Remote"], None, False),
        (["Remote - Europe"], None, True),
        (["Remote (EMEA)"], None, True),
        (["Remote"], None, False),
        (["Somewhere small"], ["DE"], True),
        (["Zürich"], None, False),
        (["Amsterdam", "Munich"], None, True),
    ],
)
def test_in_germany(locations, codes, expected):
    assert in_germany(locations, codes) is expected


def test_city_of_uses_display_names():
    assert city_of("Köln") == "Cologne"
    assert city_of("Office: Munich, Bavaria") == "Munich"
    assert city_of("Frankfurt am Main") == "Frankfurt"
    assert city_of("Paris") == ""


def test_city_requires_whole_word():
    assert city_of("Ulmenstraße, Somewhere") == ""


def test_is_remote():
    assert is_remote("Remote, Germany")
    assert is_remote("Berlin / Homeoffice")
    assert not is_remote("Berlin")
