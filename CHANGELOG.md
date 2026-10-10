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
