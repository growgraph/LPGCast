"""Command line: ``lpgcast`` (alias ``text2lpg``)."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import click
from graflo.architecture.schema.context import instance_json_schema, render_type_sheet

from lpgcast import __version__
from lpgcast.config import LPGCastSettings
from lpgcast.episode import Episode, read_episodes
from lpgcast.schema_io import load_schema
from lpgcast.select import SelectionConfig, SelectionError, select


@click.group()
@click.version_option(__version__, prog_name="lpgcast")
def main() -> None:
    """Cast text into a labeled property graph against a governed GraFlo schema."""


@main.command()
@click.option(
    "--schema",
    "schema_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="GraFlo schema or manifest (YAML or JSON).",
)
@click.option(
    "--json-schema",
    "as_json_schema",
    is_flag=True,
    help="Print the JSON Schema of the reply instead of the type sheet.",
)
def sheet(schema_path: Path, as_json_schema: bool) -> None:
    """Print what a model is shown for SCHEMA. Makes no model call."""
    schema = load_schema(schema_path)
    if as_json_schema:
        click.echo(json.dumps(instance_json_schema(schema), indent=2))
    else:
        click.echo(render_type_sheet(schema), nl=False)


@main.command("select")
@click.option(
    "--schema",
    "schema_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="GraFlo schema or manifest (YAML or JSON).",
)
@click.option("--text", help="A single text to select for.")
@click.option(
    "--episodes",
    "episodes_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Episodes, one JSON object per line.",
)
@click.option(
    "--sheet", "show_sheet", is_flag=True, help="Print each slice's type sheet."
)
def select_command(
    schema_path: Path, text: str | None, episodes_path: Path | None, show_sheet: bool
) -> None:
    """Show the slice of SCHEMA each text would be cast against. Makes no model call.

    Prints one JSON line per text: the mode, the seeds and how each lane
    ranked them, the retrieval metrics and the slice's vertex and edge counts.
    """
    if (text is None) == (episodes_path is None):
        raise click.UsageError("Give exactly one of --text or --episodes.")
    settings = LPGCastSettings()
    config = SelectionConfig(
        max_tokens=settings.slice_max_tokens, max_elements=settings.slice_max_elements
    )
    schema = load_schema(schema_path)
    episodes: Iterable[Episode]
    if text is not None:
        episodes = [Episode(text=text, source_id="text")]
    else:
        assert episodes_path is not None
        episodes = read_episodes(episodes_path)
    failed = False
    for episode in episodes:
        try:
            selection = select(schema, episode.text, config)
        except SelectionError as error:
            failed = True
            click.echo(
                json.dumps(
                    {
                        "source_id": episode.source_id,
                        "error": error.reason,
                        "message": str(error),
                    }
                )
            )
            continue
        if show_sheet:
            click.echo(f"# {episode.source_id} ({selection.mode})")
            click.echo(render_type_sheet(selection.slice), nl=False)
            continue
        core = selection.slice.core_schema
        record = {
            "source_id": episode.source_id,
            "mode": selection.mode,
            "seeds": [
                {
                    "seed": hit.vertex or list(hit.edge_id or ()),
                    "score": round(hit.score, 4),
                    "ranks": hit.ranks,
                }
                for hit in selection.seeds
            ],
            "metrics": selection.metrics.model_dump(),
            "vertices": len(core.vertex_config.vertices),
            "edges": len(list(core.edge_config.values())),
        }
        click.echo(json.dumps(record, ensure_ascii=False))
    if failed:
        raise SystemExit(1)
