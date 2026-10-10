# LPGCast

Text to a labeled property graph, against a governed [GraFlo](https://github.com/growgraph/graflo)
schema: short texts and their source metadata in, typed vertices and edges out, each grounded in a
quote from the text.

**Status: early development.** The model client and the `sheet` command are in place; extraction
(`lpgcast cast`) is not yet.

```bash
uv sync --group dev
uv run lpgcast sheet --schema schema.yaml                 # what a model is shown; no model call
uv run lpgcast sheet --schema schema.yaml --json-schema   # the reply format
uv run pytest
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

Variables are read from the environment only; no file is loaded.

## Licence

Apache-2.0.
