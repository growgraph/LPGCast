"""Quote location: offsets computed by LPGCast, never taken from the model."""

import pytest

from lpgcast.ground import locate

TEXT = "Ann  operates\nPress S-7, rated 200 kW."


def _at(span):
    return TEXT[span.start : span.end]


def test_exact_quote():
    span = locate("rated 200 kW", TEXT)
    assert span is not None and _at(span) == "rated 200 kW"


def test_case_and_whitespace_runs_are_ignored():
    span = locate("ann operates press s-7", TEXT)
    assert span is not None
    assert _at(span) == "Ann  operates\nPress S-7"


def test_surrounding_punctuation_is_ignored():
    span = locate('"200 kW."', TEXT)
    assert span is not None and _at(span) == "200 kW"


@pytest.mark.parametrize("quote", ["", "   ", "400 kW", "Bob operates"])
def test_absent_quotes_are_not_found(quote):
    assert locate(quote, TEXT) is None


def test_offsets_survive_characters_that_fold_to_two():
    text = "Straße 5, İzmir"
    span = locate("izmir", text)
    assert span is not None
    assert text[span.start : span.end] == "İzmir"
