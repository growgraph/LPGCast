"""Paired comparison of two benchmark reports."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from click.testing import CliRunner

from lpgcast.bench.cli import main as bench
from lpgcast.bench.compare import CompareError, compare, to_markdown
from lpgcast.bench.corpus import load_corpus
from lpgcast.bench.run import BenchReport, Row, new_report, run_row
from lpgcast.config import LPGCastSettings


@pytest.fixture(scope="module")
def oracle_report() -> BenchReport:
    cases = [case for case in load_corpus() if case.family in ("direction", "units")]
    row = asyncio.run(run_row(cases, LPGCastSettings(), oracle=True))
    return new_report("dev", "2026-01-01T00:00:00+00:00", [row], None)


def _with_loss(report: BenchReport, label: str = "model-b") -> BenchReport:
    """*report* relabelled, its first episode's entities all missed and failed."""
    data = report.model_copy(deep=True)
    row: Row = data.rows[0]
    row.label = label
    episode = row.cases[0].episodes[0]
    episode.status = "failed"
    episode.counts.entities_matched = 0
    episode.counts.edges_matched = 0
    episode.counts.props_matched = 0
    return data


def test_a_report_against_itself_changes_nothing(oracle_report: BenchReport):
    result = compare(oracle_report, oracle_report)
    assert result.paired == sum(len(c.episodes) for c in oracle_report.rows[0].cases)
    assert all(r.delta in (0.0, None) for r in result.rates)
    assert all(r.low == r.high == 0.0 for r in result.rates if r.delta is not None)
    assert result.wins == result.losses == 0
    assert result.ties == result.paired
    assert result.drops == result.rises == []
    assert result.transitions["ok"]["ok"] == result.paired


def test_a_lost_episode_is_a_loss_and_a_drop(oracle_report: BenchReport):
    worse = _with_loss(oracle_report)
    result = compare(oracle_report, worse)
    assert (result.row_a, result.row_b) == ("oracle", "model-b")
    assert result.losses == 1 and result.wins == 0
    first = oracle_report.rows[0].cases[0]
    assert [(d.case, d.source_id) for d in result.drops] == [
        (first.name, first.episodes[0].source_id)
    ]
    assert result.transitions["ok"]["failed"] == 1
    entity = next(r for r in result.rates if r.rate == "entity_f1")
    assert entity.delta is not None and entity.delta < 0
    assert entity.low is not None and entity.high is not None
    assert entity.low <= entity.delta <= entity.high


def test_the_comparison_is_byte_stable(oracle_report: BenchReport):
    worse = _with_loss(oracle_report)
    assert to_markdown(compare(oracle_report, worse)) == to_markdown(
        compare(oracle_report, worse)
    )


def test_different_corpora_are_refused(oracle_report: BenchReport):
    other = oracle_report.model_copy(update={"corpus_digest": "0" * 64})
    with pytest.raises(CompareError, match="different corpora"):
        compare(oracle_report, other)


def test_unpaired_episodes_are_listed_and_left_out(oracle_report: BenchReport):
    fewer = oracle_report.model_copy(deep=True)
    dropped = fewer.rows[0].cases.pop()
    result = compare(oracle_report, fewer)
    assert result.only_a == sorted(
        f"{dropped.name}/{e.source_id}" for e in dropped.episodes
    )
    assert result.only_b == []
    assert result.paired == compare(oracle_report, oracle_report).paired - len(
        dropped.episodes
    )


def test_an_ambiguous_row_must_be_named(oracle_report: BenchReport):
    two = oracle_report.model_copy(deep=True)
    two.rows = [
        _with_loss(oracle_report, "m1").rows[0],
        _with_loss(oracle_report, "m2").rows[0],
    ]
    with pytest.raises(CompareError, match="name one"):
        compare(oracle_report, two)
    assert compare(oracle_report, two, row_b="m2").row_b == "m2"
    with pytest.raises(CompareError, match="no row"):
        compare(oracle_report, two, row_b="m3")


def test_the_command_compares_two_files(oracle_report: BenchReport, tmp_path: Path):
    a, b, out = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "cmp.json"
    a.write_text(oracle_report.model_dump_json())
    b.write_text(_with_loss(oracle_report).model_dump_json())
    result = CliRunner().invoke(bench, ["compare", str(a), str(b), "--json", str(out)])
    assert result.exit_code == 0, result.output
    assert "# model-b against oracle" in result.output
    assert "Largest drops" in result.output
    assert '"losses": 1' in out.read_text()


def test_the_command_refuses_different_corpora(
    oracle_report: BenchReport, tmp_path: Path
):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(oracle_report.model_dump_json())
    b.write_text(
        oracle_report.model_copy(update={"corpus_digest": "0" * 64}).model_dump_json()
    )
    result = CliRunner().invoke(bench, ["compare", str(a), str(b)])
    assert result.exit_code != 0
    assert "different corpora" in result.output
