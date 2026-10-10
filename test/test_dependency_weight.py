"""LPGCast stays light: six runtime dependencies and a small import footprint."""

import re
import subprocess
import sys
from importlib.metadata import distributions, requires

RUNTIME = {"click", "graflo", "openai", "pydantic", "pydantic-settings", "pyyaml"}

#: Never installed alongside LPGCast.
NOT_INSTALLED = ("langchain", "langgraph", "torch")

#: Never loaded by importing LPGCast. graflo installs some of these for its own
#: database and RDF features; LPGCast's import path must not reach them.
NOT_IMPORTED = (
    "langchain",
    "langchain_core",
    "langgraph",
    "torch",
    "numpy",
    "pandas",
    "rdflib",
    "sklearn",
)


def _name(requirement: str) -> str:
    return re.split(r"[\s<>=!~;\[]", requirement, maxsplit=1)[0].lower()


def test_declares_exactly_the_runtime_dependencies():
    declared = {
        _name(req) for req in requires("lpgcast") or [] if "extra ==" not in req
    }
    assert declared == RUNTIME


def test_heavy_frameworks_are_not_installed():
    installed = {(dist.metadata["Name"] or "").lower() for dist in distributions()}
    offending = sorted(
        name
        for name in installed
        if any(
            name == banned or name.startswith(f"{banned}-") for banned in NOT_INSTALLED
        )
    )
    assert offending == []


def test_import_loads_nothing_heavy():
    probe = (
        "import sys, lpgcast, lpgcast.cli, lpgcast.config, lpgcast.llm, "
        "lpgcast.schema_io\n"
        f"print(','.join(m for m in {NOT_IMPORTED!r} if m in sys.modules))"
    )
    loaded = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert loaded == ""
