# LPGCast

Text to a labeled property graph, against a governed [GraFlo](https://github.com/growgraph/graflo)
schema: short texts and their source metadata in, typed vertices and edges out, each grounded in a
quote from the text.

**Status: early development, not yet released.**

```bash
uv sync --group dev
uv run lpgcast cast --schema schema.yaml --episodes episodes.jsonl --out out/   # extract
uv run lpgcast cast ... --db conn.yaml        # and write to a graflo connection
uv run lpgcast cast ... --replay              # rerun from the cache; makes no request
uv run lpgcast sheet --schema schema.yaml     # what a model is shown; no model call
uv run lpgcast select --schema schema.yaml --episodes episodes.jsonl   # the slice per text
uv run pytest
```

An episodes file holds one JSON object per line:

```json
{"source_id": "msg-1", "text": "Ann now operates station S-7.", "reference_time": "2024-03-04T09:15:00Z"}
```

A connection file is a graflo connection config, e.g. `db_type: graflo_backend` with
`output_dir: db/`, or `db_type: neo4j` with `uri`, `username` and `password`.

## What a cast does

Per episode: choose the slice of the schema the text is about; ask the model once, in a flat reply
format; check the reply (types, relations, properties, values, identities, and every quote against
the text); ask for corrections at most twice; quarantine what still fails; compute identities;
assemble a graflo `GraphContainer`. Under `--out`:

| File | Holds |
|---|---|
| `graph.json` | the schema and the graph |
| `groundings.jsonl` | the text span of every vertex, edge and property |
| `quarantine.jsonl` | items left out, failed episodes, and `unmapped` text no type covers |
| `pending.jsonl` | edges to an entity named only by a secondary identity, resolved at write |
| `episodes.jsonl` | one result per episode |
| `manifest.json` | versions, settings, counts and token usage |

Everything but `manifest.json` is byte-identical when a cast is replayed. An entity the text only
refers to is looked up, never created. Writing upserts by identity, so writing a cast twice changes
nothing in a database that upserts; graflo's file backend appends instead.

## Model settings

Any OpenAI-compatible endpoint — OpenAI, Ollama (`/v1`), vLLM — configured by environment
variables:

| Variable | Meaning |
|---|---|
| `LPGCAST_LLM_MODEL` | Model name. Required. |
| `LPGCAST_LLM_BASE_URL` | Endpoint, e.g. `http://localhost:11434/v1`. Unset means OpenAI. |
| `LPGCAST_LLM_API_KEY` | Required for any request; any value for a local endpoint. Without it only cached responses are served. |
| `LPGCAST_LLM_RESPONSE_FORMAT` | `auto` (default), `json_schema` or `json_object`. |
| `LPGCAST_CACHE_DIR` | Response cache directory. |
| `LPGCAST_CACHE_REQUIRE_HIT` | A cache miss raises instead of calling the model. |
| `LPGCAST_MAX_EPISODE_TOKENS` | Longer episodes are refused, never chunked (default 4000, estimated as characters / 4). |
| `LPGCAST_SLICE_MAX_TOKENS`, `LPGCAST_SLICE_MAX_ELEMENTS` | Budget of the schema slice a model is shown. |

Variables are read from the environment only; no file is loaded.

## Licence

Apache-2.0.
