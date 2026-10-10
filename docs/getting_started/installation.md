# Installation

LPGCast needs Python 3.11 or later and graflo 1.17 or later.

```bash
uv add lpgcast        # or: pip install lpgcast
```

Until the first release is on PyPI, install from a clone:

```bash
git clone https://github.com/growgraph/LPGCast
cd LPGCast
uv sync --group dev
```

## What it installs

Six runtime dependencies and nothing else: `graflo`, `openai`, `pydantic`,
`pydantic-settings`, `click` and `pyyaml`. There is no LangChain, no encoder
and no vector store; a test keeps it that way.

| Command | What it is |
|---|---|
| `lpgcast` (alias `text2lpg`) | `sheet`, `select` and `cast`; see [Command line](../reference/cli.md) |
| `lpgcast-bench` | the [benchmark](../guides/benchmark.md) |

## Pointing it at a model

Any OpenAI-compatible endpoint: OpenAI itself, Ollama's `/v1`, vLLM. Settings
come from environment variables only; no file is read.

=== "OpenAI"

    ```bash
    export LPGCAST_LLM_API_KEY=sk-...
    # LPGCAST_LLM_MODEL defaults to gpt-5.6-luna
    ```

=== "Ollama"

    ```bash
    export LPGCAST_LLM_BASE_URL=http://localhost:11434/v1
    export LPGCAST_LLM_MODEL=qwen3:8b
    export LPGCAST_LLM_API_KEY=local   # any value; without a key only cached replies are served
    ```

=== "vLLM"

    ```bash
    export LPGCAST_LLM_BASE_URL=http://localhost:8000/v1
    export LPGCAST_LLM_MODEL=<served model name>
    export LPGCAST_LLM_API_KEY=local
    ```

Without an API key LPGCast makes no request at all, and serves only replies it
has cached. Every setting is listed in [Settings](../reference/settings.md).
