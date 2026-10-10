"""Groundings: where in the text each assertion was read.

The model copies a quote; LPGCast finds it in the episode and records the
character offsets. Offsets are never taken from the model. A quote that cannot
be found is a hallucination flag, handled by validation.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime
from typing import Any, Literal

from graflo.architecture.graph_types.identifiers import EdgeId
from pydantic import BaseModel, Field

_EDGE_PUNCTUATION = " \t\r\n.,;:!?\"'`()[]{}«»“”‘’"


class Span(BaseModel):
    """Character offsets into an episode's text, end exclusive."""

    start: int
    end: int


def _fold(char: str) -> str:
    decomposed = unicodedata.normalize("NFKD", char)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def _normalized(text: str) -> tuple[str, list[int]]:
    """Whitespace runs collapsed to one space, case and accents folded, with
    each output character's index in *text*."""
    out: list[str] = []
    index: list[int] = []
    in_space = False
    for position, char in enumerate(text):
        if char.isspace():
            if not in_space:
                out.append(" ")
                index.append(position)
            in_space = True
            continue
        in_space = False
        for folded in _fold(char):
            out.append(folded)
            index.append(position)
    return "".join(out), index


def locate(quote: str, text: str) -> Span | None:
    """Find *quote* in *text*: exactly, then ignoring case, accents and
    whitespace runs, then also without surrounding punctuation. Returns the
    first match."""
    if not quote.strip():
        return None
    start = text.find(quote)
    if start != -1:
        return Span(start=start, end=start + len(quote))
    haystack, index = _normalized(text)
    for candidate in (quote, quote.strip(_EDGE_PUNCTUATION)):
        needle = _normalized(candidate.strip())[0]
        if not needle:
            continue
        found = haystack.find(needle)
        if found != -1:
            return Span(start=index[found], end=index[found + len(needle) - 1] + 1)
    return None


class Grounding(BaseModel):
    """One assertion and the span of text it was read from.

    Carried in the cast result only; nothing here is written to the graph.
    """

    source_id: str = Field(description="Episode the assertion was read from.")
    kind: Literal["vertex", "edge", "property"]
    vertex: str | None = Field(
        default=None, description="Vertex type, for a vertex or its property."
    )
    identity: dict[str, Any] | None = Field(
        default=None, description="Identity of the vertex, as written or looked up by."
    )
    edge: EdgeId | None = Field(
        default=None, description="Edge, for an edge or its property."
    )
    source_identity: dict[str, Any] | None = None
    target_identity: dict[str, Any] | None = None
    property: str | None = Field(
        default=None, description="Property name, for a property."
    )
    char_start: int
    char_end: int
    quote: str = Field(description="The text at the span, as it stands in the episode.")
    extractor: str = Field(description="``lpgcast/<version>``.")
    model: str | None = Field(
        default=None, description="Model that produced the reply."
    )
    schema_ref: str = Field(description="``<schema name>@<version>``.")
    reference_time: datetime | None = None
