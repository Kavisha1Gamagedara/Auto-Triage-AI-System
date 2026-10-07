"""Tests for the Agent 4 part name resolver.

Runs against the live catalog via get_db(), matching how the other backend
tests in this project are written. The resolver is built once per module -
constructing it builds a BM25 index over every catalog name.
"""

import pytest

from agent4_resolver import PartResolver
from db import get_db


@pytest.fixture(scope="module")
def resolver():
    return PartResolver(get_db())


def test_exact_alias_hit(resolver):
    """A known trade term resolves through the alias table at full confidence."""
    result = resolver.resolve("dynamo")

    assert result["canonical"] == "Alternator"
    assert result["method"] == "alias_exact"
    assert result["confidence"] == 1.0
    assert result["candidates"] == []


def test_exact_catalog_name(resolver):
    """A canonical name matches itself without falling through to ranking."""
    result = resolver.resolve("Brake Pads")

    assert result["canonical"] == "Brake Pads"
    assert result["method"] == "exact"
    assert result["confidence"] == 1.0


def test_reordered_multiword_query_uses_bm25(resolver):
    """Word order does not matter to BM25, so a scrambled phrase still lands."""
    result = resolver.resolve("sensor mass air")

    assert result["canonical"] == "Mass Air Flow Sensor"
    assert result["method"] == "bm25"
    assert 0.45 <= result["confidence"] <= 1.0
    # BM25 returns numpy scalars; they must be cast or FastAPI cannot
    # serialise the response.
    assert isinstance(result["confidence"], float)


def test_typo_falls_through_to_fuzzy(resolver):
    """A misspelling shares no whole token, so only fuzzy can catch it.

    'Altenator' is used rather than 'MAF senser': 'maf' is itself an alias
    key, so that query is now caught earlier by the n-gram pre-pass. See
    test_embedded_alias_beats_fuzzy_for_maf.
    """
    result = resolver.resolve("Altenator")

    assert result["canonical"] == "Alternator"
    assert result["method"] == "fuzzy"
    assert result["confidence"] >= 0.8


def test_embedded_alias_in_longer_query(resolver):
    """A trade term surrounded by symptom words still resolves.

    This is the Run 1 failure mode: 'dynamo' resolved but 'dynamo not
    charging' did not, because BM25's corpus holds canonical names only and
    fuzzy's whole-string ratio was diluted below its floor by the extra token.
    """
    for query, expected in [
        ("dynamo not charging", "Alternator"),
        ("shockers gone", "Shock Absorber"),
        ("silencer rusted", "Muffler"),
        ("windshield crack", "Windscreen"),
        ("wishbone bush gone", "Control Arm"),
        ("dicky door dented", "Rear Hatch"),
    ]:
        result = resolver.resolve(query)
        assert result["canonical"] == expected, (query, result)
        assert result["method"] == "alias_partial"
        assert result["confidence"] == 0.9


def test_embedded_alias_beats_fuzzy_for_maf(resolver):
    """'maf' is an alias key, so the pre-pass claims it before fuzzy runs."""
    result = resolver.resolve("MAF senser dirty")

    assert result["canonical"] == "Mass Air Flow Sensor"
    assert result["method"] == "alias_partial"


def test_longest_ngram_wins(resolver):
    """'dicky door' must beat the shorter 'door' inside the same query."""
    assert resolver.resolve("dicky door dented")["canonical"] == "Rear Hatch"


def test_ambiguous_embedded_aliases_do_not_guess(resolver):
    """Two different parts named in one query fall through to ranking.

    'pads' and 'rotor' are aliases for different parts. The pre-pass must not
    silently pick one; deciding between them is ranking's job.
    """
    result = resolver.resolve("pads and rotor both worn")

    assert result["method"] != "alias_partial"


def test_unresolvable_query_fails_honestly(resolver):
    """An unknown part is reported as unresolved, never guessed."""
    result = resolver.resolve("flux capacitor")

    assert result["canonical"] is None
    assert result["method"] == "none"
    assert result["confidence"] == 0.0
    assert len(result["candidates"]) > 0


def test_rear_bumper_does_not_resolve_to_front_bumper(resolver):
    """Regression: exact precedence must beat a reduced-form alias hit.

    'bumper' is an alias for Front Bumper. An earlier version normalised the
    query before every exact lookup, so 'Rear Bumper' reduced to 'bumper' and
    returned Front Bumper at confidence 1.0 - a confidently wrong part.
    The full string must be matched against the catalog before the
    stopword-stripped form is matched against the alias table.
    """
    result = resolver.resolve("Rear Bumper")

    assert result["canonical"] == "Rear Bumper"
    assert result["canonical"] != "Front Bumper"
    assert result["confidence"] == 1.0

    # The companion case must keep working: 'rear buffer' is a genuine alias.
    assert resolver.resolve("rear buffer")["canonical"] == "Rear Bumper"
    assert resolver.resolve("front buffer")["canonical"] == "Front Bumper"
