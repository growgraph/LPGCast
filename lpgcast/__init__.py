"""LPGCast: text to a labeled property graph, against a governed GraFlo schema."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lpgcast")
except PackageNotFoundError:  # running from a source tree without install
    __version__ = "0.0.0"
