"""LPGCast: text to a labeled property graph, against a governed GraFlo schema.

The names below load on first use, so ``import lpgcast`` stays light.
"""

from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any

try:
    __version__ = version("lpgcast")
except PackageNotFoundError:  # running from a source tree without install
    __version__ = "0.0.0"

if TYPE_CHECKING:
    from lpgcast.cast import CastResult, EpisodeResult, LPGCaster
    from lpgcast.config import CacheSettings, LLMSettings, LPGCastSettings
    from lpgcast.episode import Episode, read_episodes
    from lpgcast.ground import Grounding
    from lpgcast.output import save_cast
    from lpgcast.schema_io import load_schema
    from lpgcast.sink import JsonlQuarantineSink, MemoryQuarantineSink
    from lpgcast.write import WriteReport, load_connection, write_cast

_EXPORTS: dict[str, str] = {
    "CacheSettings": "lpgcast.config",
    "CastResult": "lpgcast.cast",
    "Episode": "lpgcast.episode",
    "EpisodeResult": "lpgcast.cast",
    "Grounding": "lpgcast.ground",
    "JsonlQuarantineSink": "lpgcast.sink",
    "LLMSettings": "lpgcast.config",
    "LPGCastSettings": "lpgcast.config",
    "LPGCaster": "lpgcast.cast",
    "MemoryQuarantineSink": "lpgcast.sink",
    "WriteReport": "lpgcast.write",
    "load_connection": "lpgcast.write",
    "load_schema": "lpgcast.schema_io",
    "read_episodes": "lpgcast.episode",
    "save_cast": "lpgcast.output",
    "write_cast": "lpgcast.write",
}

__all__ = [
    "CacheSettings",
    "CastResult",
    "Episode",
    "EpisodeResult",
    "Grounding",
    "JsonlQuarantineSink",
    "LLMSettings",
    "LPGCastSettings",
    "LPGCaster",
    "MemoryQuarantineSink",
    "WriteReport",
    "__version__",
    "load_connection",
    "load_schema",
    "read_episodes",
    "save_cast",
    "write_cast",
]


def __getattr__(name: str) -> Any:
    module = _EXPORTS.get(name)
    if module is None:
        raise AttributeError(f"module 'lpgcast' has no attribute {name!r}")
    value = getattr(importlib.import_module(module), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
