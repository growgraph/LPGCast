# Support tickets

Five short texts from a support desk, cast into a small schema: customers, agents, tickets,
products, tags and comments.

| File | Holds |
|---|---|
| `schema.yaml` | the governed schema: identities, a secondary identity, a unit, a blank type |
| `episodes.jsonl` | five texts with their source id, time and channel |

What the episodes exercise:

- `mail-1041` states a customer, a ticket and a product, with typed properties.
- `chat-2207` writes a date in words, and an edge property.
- `mail-1042` names a customer by email only: the edge waits for a lookup at write time.
- `note-88` adds a comment (a blank type) and a wait in hours.
- `chat-2210` is an instruction, not a statement: nothing should be written from it.

Look first; neither command calls a model:

```bash
uv run lpgcast sheet --schema examples/tickets/schema.yaml
uv run lpgcast select --schema examples/tickets/schema.yaml --episodes examples/tickets/episodes.jsonl
```

Cast, with `LPGCAST_LLM_API_KEY` set (and `LPGCAST_LLM_BASE_URL` / `LPGCAST_LLM_MODEL` for a
local server):

```bash
uv run lpgcast cast --schema examples/tickets/schema.yaml \
    --episodes examples/tickets/episodes.jsonl --out out/tickets
```

Write it to a database too with `--db examples/connections/neo4j.yaml`, or to files with
`--db examples/connections/file-backend.yaml`.
