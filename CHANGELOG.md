# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Package skeleton**: `lpgcast` on Python ≥ 3.11 with six runtime dependencies (`graflo`, `openai`,
  `pydantic`, `pydantic-settings`, `click`, `pyyaml`).
- **Settings** from `LPGCAST_LLM_*`, `LPGCAST_CACHE_*` and `LPGCAST_*` variables only; no `.env` file
  is read.
- **`LLMClient.acomplete_json`**: one JSON object per request from any OpenAI-compatible endpoint;
  strict `json_schema` output with a `json_object` fallback, tolerant parsing, re-ask on malformed
  JSON, one re-issue on timeout, typed configuration errors.
- **Response cache** keyed on the logical request, written atomically; read-only mode and
  `LPGCAST_CACHE_REQUIRE_HIT` for replays that make no request. Without an API key only cached
  responses are served.
- **Usage accounting**: calls, failures and tokens, with billed tokens kept apart from tokens
  replayed from the cache; `track_usage()` scopes it per task.
- **CLI** `lpgcast` (alias `text2lpg`) with `sheet`: the type sheet, or with `--json-schema` the
  reply schema, for a schema or manifest file.
- **Episodes** (`Episode`, `read_episodes`): text, source id, reference time, metadata (never shown
  to the model) and thread context, from JSON Lines.
- **Schema selection** (`select`): exact-form, phrase and number-unit lanes fused by rank, a relative
  relevance gate, and closure by graflo's `subschema()` under a budget; a schema under budget passes
  whole, and a large schema nothing matches is a `SelectionError` with a reason.
- **Extraction prompt** (`build_messages`): byte-deterministic, type sheet and rules first, the text
  inside a tagged block it cannot close.
- **`extract`**: one call per episode in the flat reply format, parsed into wire models; an episode
  over `LPGCAST_MAX_EPISODE_TOKENS` is refused before any call.
- **CLI** `lpgcast select`: the slice each text would be cast against, as JSON lines or type sheets.
