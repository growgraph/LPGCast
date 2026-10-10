# LPGCast

Text to a labeled property graph, against a governed [GraFlo](https://github.com/growgraph/graflo)
schema: short texts and their source metadata in, typed vertices and edges out, each grounded in a
quote from the text.

**Status: early development.** Schema selection, the prompt and the extraction call are in place;
validation, identity resolution and writing (`lpgcast cast`) are not yet.

```bash
uv sync --group dev
uv run lpgcast sheet --schema schema.yaml                 # what a model is shown; no model call
uv run lpgcast sheet --schema schema.yaml --json-schema   # the reply format
uv run lpgcast select --schema schema.yaml --episodes episodes.jsonl   # the slice per text
uv run pytest
```

An episodes file holds one JSON object per line:

```json
{"source_id": "msg-1", "text": "Ann now operates station S-7.", "reference_time": "2024-03-04T09:15:00Z"}
```

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
