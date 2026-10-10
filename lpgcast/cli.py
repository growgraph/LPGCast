"""Command line: ``lpgcast`` (alias ``text2lpg``)."""

from __future__ import annotations

import json
from pathlib import Path

import click
from graflo.architecture.schema.context import instance_json_schema, render_type_sheet

from lpgcast import __version__
from lpgcast.schema_io import load_schema


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
