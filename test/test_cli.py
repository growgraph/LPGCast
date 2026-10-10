"""The lpgcast command line."""

import json
from importlib.metadata import entry_points

from click.testing import CliRunner
from conftest import DATA

from lpgcast.cli import main


def test_sheet_prints_the_type_sheet():
    result = CliRunner().invoke(main, ["sheet", "--schema", str(DATA / "schema.yaml")])
    assert result.exit_code == 0, result.output
    assert (
        'Machine  "A production machine."  ~ unit; station  id: serial' in result.output
    )
    assert "power FLOAT [kW]" in result.output
    assert result.output.rstrip().endswith("does not exist.")


def test_sheet_reads_a_manifest():
    result = CliRunner().invoke(
        main, ["sheet", "--schema", str(DATA / "manifest.yaml")]
    )
    assert result.exit_code == 0, result.output
    assert "Machine  id: serial" in result.output


def test_sheet_prints_the_reply_schema():
    result = CliRunner().invoke(
        main, ["sheet", "--schema", str(DATA / "schema.yaml"), "--json-schema"]
    )
    assert result.exit_code == 0, result.output
    shape = json.loads(result.output)
    vertex = shape["properties"]["vertices"]["items"]
    assert vertex["properties"]["type"]["enum"] == ["Machine", "Person", "WorkOrder"]


def test_text2lpg_is_an_alias():
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts["text2lpg"] == scripts["lpgcast"] == "lpgcast.cli:main"
