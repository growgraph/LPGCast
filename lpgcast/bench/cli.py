"""``lpgcast-bench``: cast the corpus and score it."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import click

from lpgcast.bench.corpus import CORPUS_VERSION, BenchCase, load_corpus
from lpgcast.bench.report import to_markdown, write_report
from lpgcast.bench.run import Row, load_prices, new_report, run_row
from lpgcast.config import LPGCastSettings
from lpgcast.llm.cache import CacheMissError
from lpgcast.llm.client import LLMConfigurationError


def select_cases(
    corpus: list[BenchCase],
    split: str,
    families: tuple[str, ...],
    cases: tuple[str, ...],
) -> list[BenchCase]:
    """Narrow *corpus* by split, family and case name; filters compose."""
    selected = corpus if split == "all" else [c for c in corpus if c.split == split]
    if families:
        selected = [c for c in selected if c.family in families]
    if cases:
        selected = [c for c in selected if c.name in cases]
    return selected


@click.command()
@click.option(
    "--model",
    "models",
    multiple=True,
    metavar="NAME",
    help="Model to benchmark, repeatable; the endpoint is LPGCAST_LLM_BASE_URL. "
    "Without it only the free oracle row runs.",
)
@click.option(
    "--oracle/--no-oracle",
    default=True,
    show_default=True,
    help="Add the oracle row: the expected graph through the whole pipeline. Free.",
)
@click.option(
    "--split",
    type=click.Choice(["dev", "test", "all"]),
    default="all",
    show_default=True,
    help="dev is tuned against; only test is publishable.",
)
@click.option("--family", "families", multiple=True, help="Only these families.")
@click.option(
    "--case", "cases", multiple=True, help="Only these cases, e.g. units/lab."
)
@click.option(
    "--replay",
    is_flag=True,
    help="Serve every reply from the cache; a miss stops the run.",
)
@click.option(
    "--out",
    "out_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("bench-results"),
    show_default=True,
    help="Where the JSON and Markdown reports go.",
)
@click.option("--concurrency", type=int, default=8, show_default=True)
def main(
    models: tuple[str, ...],
    oracle: bool,
    split: str,
    families: tuple[str, ...],
    cases: tuple[str, ...],
    replay: bool,
    out_dir: Path,
    concurrency: int,
) -> None:
    """Benchmark text-to-graph casting against the bundled corpus."""
    settings = LPGCastSettings()
    if replay:
        settings.cache = settings.cache.model_copy(update={"require_hit": True})
    names = list(models)
    if not names and not oracle:
        raise click.UsageError("nothing to run: give --model or keep --oracle")
    selected = select_cases(load_corpus(), split, families, cases)
    if not selected:
        raise click.UsageError("no case matches the filters")
    prices, prices_source = load_prices()
    click.echo(
        f"Corpus {CORPUS_VERSION} [{split}]: {len(selected)} case(s); "
        f"rows: {', '.join((['oracle'] if oracle else []) + names)}",
        err=True,
    )
    started = datetime.now(UTC)
    rows: list[Row] = []
    try:
        if oracle:
            rows.append(
                asyncio.run(
                    run_row(selected, settings, oracle=True, concurrency=concurrency)
                )
            )
        for name in names:
            row_settings = settings.model_copy(
                update={"llm": settings.llm.model_copy(update={"model": name})}
            )
            rows.append(
                asyncio.run(
                    run_row(
                        selected, row_settings, concurrency=concurrency, prices=prices
                    )
                )
            )
    except (LLMConfigurationError, CacheMissError) as error:
        raise click.ClickException(str(error)) from error
    report = new_report(
        split, started.isoformat(timespec="seconds"), rows, prices_source
    )
    click.echo(to_markdown(report))
    json_path, md_path = write_report(
        report, out_dir, started.strftime("%Y%m%dT%H%M%SZ")
    )
    click.echo(f"Wrote {json_path} and {md_path}", err=True)
