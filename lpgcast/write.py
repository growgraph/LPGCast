"""Write a cast to a database through graflo.

The schema is defined on the target first (an existing definition is reused),
edges whose endpoint is known only by a secondary identity are looked up, and
the container is written by identity upsert through graflo's ``DBWriter``
without an ingestion resource.

graflo's database layer is imported inside these functions: it loads drivers
and dataframe libraries that a cast without a write never needs.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from graflo.architecture.graph_types.container import GraphContainer
from graflo.architecture.graph_types.identifiers import EdgeId
from graflo.architecture.schema.document import Schema
from pydantic import BaseModel, Field

from lpgcast.resolve import PendingEdge

if TYPE_CHECKING:
    from graflo.connections.onto import DBConfig

    from lpgcast.cast import CastResult

#: A secondary identity that matches several vertices names none of them.
LOOKUP_AMBIGUITY = "skip"


class WriteReport(BaseModel):
    """What was sent to the database."""

    target: str = Field(description="Connection type written to.")
    schema_defined: bool = Field(
        description="False when an existing definition was reused."
    )
    vertices: dict[str, int] = Field(description="Documents per vertex type.")
    edges: dict[str, int] = Field(
        description="Edges per edge, keyed ``source-relation-target``."
    )
    lookups_resolved: int = 0
    lookups_unresolved: int = 0


def load_connection(path: str | Path) -> DBConfig:
    """A graflo connection config from a YAML file (``db_type`` plus its fields)."""
    from graflo.connections.onto import DBConfig

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path}: expected a mapping")
    return DBConfig.from_dict(data)


def _edge_label(edge_id: EdgeId) -> str:
    return f"{edge_id[0]}-{edge_id[2] or ''}-{edge_id[1]}"


def _define(schema: Schema, conn_conf: DBConfig, recreate: bool) -> bool:
    from graflo.architecture.contract.ingestion import IngestionModel
    from graflo.architecture.contract.manifest import GraphManifest
    from graflo.db.conn import SchemaExistsError
    from graflo.hq.graph_engine import GraphEngine

    manifest = GraphManifest(
        graph_schema=schema, ingestion_model=IngestionModel(resources=[])
    )
    try:
        GraphEngine(target_db_flavor=conn_conf.connection_type).define_schema(
            manifest=manifest, target_db_config=conn_conf, recreate_schema=recreate
        )
    except SchemaExistsError:
        schema.db_profile.db_flavor = conn_conf.connection_type
        schema.finish_init()
        return False
    return True


def _resolve_pending(
    schema: Schema, conn_conf: DBConfig, pending: list[PendingEdge]
) -> tuple[dict[EdgeId, list[Any]], int, int]:
    """Look up secondary-identity endpoints; returns edges by id, resolved, unresolved."""
    from graflo.architecture.evolution.sanitize import with_physical_names
    from graflo.architecture.schema.physical_keys import PhysicalKeys
    from graflo.db.manager import ConnectionManager
    from graflo.hq.endpoint_resolve import resolve_edge_endpoints

    flavor = conn_conf.connection_type
    named = with_physical_names(schema, flavor)
    keys = PhysicalKeys(named.db_profile)
    vertex_config = named.resolve_db_aware(flavor).vertex_config

    groups: dict[tuple, list[PendingEdge]] = defaultdict(list)
    for edge in pending:
        groups[
            (
                edge.edge_id,
                tuple(sorted(edge.source.match or {})),
                tuple(sorted(edge.target.match or {})),
            )
        ].append(edge)

    resolved: dict[EdgeId, list[Any]] = defaultdict(list)
    written = dropped = 0
    with ConnectionManager(connection_config=conn_conf) as db:
        for (edge_id, source_match, target_match), edges in groups.items():
            source, target = edge_id[0], edge_id[1]
            source_identity = list(vertex_config.identity_fields(source))
            target_identity = list(vertex_config.identity_fields(target))
            docs = [
                (
                    keys.vertex_doc(source, e.source.match or e.source.identity or {}),
                    keys.vertex_doc(target, e.target.match or e.target.identity or {}),
                    e.props,
                )
                for e in edges
            ]
            triples, stats = resolve_edge_endpoints(
                db,
                docs,
                source_class=vertex_config.vertex_dbname(source),
                target_class=vertex_config.vertex_dbname(target),
                source_match_fields=keys.vertex_fields(
                    source, source_match or source_identity
                ),
                target_match_fields=keys.vertex_fields(
                    target, target_match or target_identity
                ),
                source_identity_fields=keys.vertex_fields(source, source_identity),
                target_identity_fields=keys.vertex_fields(target, target_identity),
                resolve_source=bool(source_match),
                resolve_target=bool(target_match),
                policy=LOOKUP_AMBIGUITY,
            )
            for triple in triples:
                resolved[edge_id].append(
                    (
                        keys.logical_vertex_doc(source, triple[0]),
                        keys.logical_vertex_doc(target, triple[1]),
                        triple[2],
                    )
                )
            written += stats.written
            dropped += stats.dropped
    return resolved, written, dropped


async def write_cast(
    result: CastResult, conn_conf: DBConfig, *, recreate_schema: bool = False
) -> WriteReport:
    """Write *result* to the database *conn_conf* points at.

    Vertices and edges are upserted by identity, so writing the same cast twice
    leaves a database that upserts unchanged. graflo's file backend appends on
    every write instead; count distinct identities there.
    """
    from graflo.architecture.contract.ingestion import IngestionModel
    from graflo.hq.db_writer import DBWriter

    schema = result.output.graph_schema.model_copy(deep=True)
    defined = await asyncio.to_thread(_define, schema, conn_conf, recreate_schema)
    data = result.output.data
    container = GraphContainer(
        vertices={
            name: [dict(doc) for doc in docs] for name, docs in data.vertices.items()
        },
        edges={edge_id: list(triples) for edge_id, triples in data.edges.items()},
    )

    resolved_count = unresolved_count = 0
    if result.pending:
        resolved, resolved_count, unresolved_count = await asyncio.to_thread(
            _resolve_pending, schema, conn_conf, result.pending
        )
        for edge_id, triples in resolved.items():
            container.edges.setdefault(edge_id, []).extend(triples)

    ingestion_model = IngestionModel(resources=[])
    ingestion_model.finish_init(schema.core_schema)
    report = WriteReport(
        target=str(conn_conf.connection_type),
        schema_defined=defined,
        vertices={name: len(docs) for name, docs in container.vertices.items()},
        edges={
            _edge_label(eid): len(triples) for eid, triples in container.edges.items()
        },
        lookups_resolved=resolved_count,
        lookups_unresolved=unresolved_count,
    )
    await DBWriter(schema=schema, ingestion_model=ingestion_model).write(
        gc=container, conn_conf=conn_conf, resource_name=None
    )
    return report
