# The benchmark

`lpgcast-bench` casts a corpus of short texts and scores the result against the graph each text
states. No model judges: matching is exact.

```bash
lpgcast-bench                              # the oracle row only; free
lpgcast-bench --model gpt-5.6-luna         # plus a model row (LPGCAST_LLM_* settings)
lpgcast-bench --split test --model a --model b
lpgcast-bench --model a --replay           # from the cache; makes no request
```

Each run writes `<stamp>.json` (counts per episode, rates per case and row) and `<stamp>.md`
under `--out` (default `bench-results/`, ignored by git). Set `LPGCAST_BENCH_PRICES` to a JSON
file `{"<model>": {"input_per_1m": …, "output_per_1m": …}, "_source": "…"}` for a cost column;
no prices ship with the package.

## Corpus

`lpgcast/bench/cases/<family>/<instance>/` holds `case.yaml` (description, schema, and optionally `recast: true`
or pinned `settings`), `episodes.jsonl` and `expected.yaml`. Schemas live in `lpgcast/bench/schemas/`; a case
naming several merges their vertices and edges. Each family isolates one failure mode in four
domains:

| Family | What it isolates |
|---|---|
| `direction` | same-type relations, passive voice, the target named first |
| `units` | declared units, grouped digits, written-out dates and integers, yes/no flags |
| `identity` | entities the text gives no identity, which must not be written |
| `mention` | entities known by a secondary identity only; earlier assigned or blank entities that must not be minted again |
| `recast` | a second cast with a fresh model call |
| `injection` | instructions inside the text |
| `distractors` | a wide schema sliced under a tight budget, with types the text names but says nothing about |

`expected.yaml` maps each episode to `vertices` (keyed by a handle), `edges` between handles, and
`forbidden` items a cast must not write. Every quote occurs in the text and every value is what
its field makes of it; a test checks both, and that the oracle scores perfectly on the whole
schema.

`SPLITS.yaml` puts two instances of each family in `dev` and two in `test`. Tune against `dev`;
only `--split test` on an unmodified corpus is publishable, and a report says when it is not.
`CORPUS_VERSION` identifies the corpus and `CORPUS_DIGEST` pins it: change a case, a schema or the
split and bump the version, or the test suite fails. Results from different versions are not
comparable.

## Rows

- **oracle** replies with the expected graph through the whole pipeline. It is the ceiling the
  pipeline allows: what selection leaves out of the slice costs it too.
- **a model** row per `--model`, against `LPGCAST_LLM_BASE_URL`.

## Metrics

Every metric is a ratio of counts pooled over episodes.

| Metric | Counts |
|---|---|
| Conformance | items of the first reply with no schema finding, over items emitted; *final* is the attempt kept |
| Type / relation / property hallucination | `unknown_type`, `undeclared_edge`, `undeclared_property` findings on the first reply, over vertices, edges, properties emitted |
| Ungrounded | first-reply quotes not found in the text, over items emitted |
| Entity, edge, property P/R/F1 | matched over produced and over expected; properties on matched entities and edges only |
| Direction | edges matched, over edges matched or found the wrong way round |
| Span | matched items whose quote overlaps the expected one |
| Mention | matched entities whose `mention` flag agrees |
| Forbidden | forbidden vertices written, and forbidden edges produced |
| Seed / closure recall | expected types among the seeds and in the slice, read on sliced episodes only |
| Re-cast added / duplicated | natural or hash identities a second cast adds; assigned or blank vertices it mints anew |
| Tokens, requests per episode | billed and cache-replayed tokens alike |

Hallucination is measured against the slice the model was shown, so a type selection left out
counts as well; the oracle row separates the two.

Entities match by identity: a natural type's key, a hash type's digest, or any complete secondary
identity. An assigned or blank type matches by equal property values or an overlapping quote.
Values compare after coercion by their field; strings ignore case and runs of whitespace.

## Adding a case

In a clone: write the three files under a new instance directory, add it to
`SPLITS.yaml`, run `uv run pytest test/test_bench.py`, and set `CORPUS_DIGEST` in
`lpgcast/bench/corpus.py` to the value the failing digest test prints, with a
new `CORPUS_VERSION`.
