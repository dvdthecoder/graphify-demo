# 5. Questions you can ask

A built graph supports three kinds of question. All of them take `--graph <path>`, so a merged graph can be queried without overwriting a repo's own `graph.json`.

```bash
graphify query "how do bids flow from harvest to report" --graph cross-repo-graph.json
graphify path "phrase_profile()" "ServeL40S"            --graph cross-repo-graph.json
graphify explain "call_local_llm()"                     --graph cross-repo-graph.json
```

| Command | Traversal | Good for |
|---|---|---|
| `query "<q>"` | BFS from matched nodes (`--dfs` for depth-first, `--budget N` to cap tokens) | Broad context: "what touches X?", "how does stage Y work?" |
| `path A B` | Shortest path | "Is there any connection between A and B?" |
| `explain X` | Node plus its neighbourhood | "What is this and why does it exist?" |

## Question patterns that work well

**Structure and ownership**

- What are the hub nodes? (In drone-okg: `db.py` with 124 edges, `Connection` 73, `connect()` 45, `report_sparklines.py` 42.)
- Which modules write to the database, and which only read?
- What does the agent's MCP server expose, and which scripts back each tool?

**Rationale ("why")**

- Why is local inference not the default? (Answered by a `rationale_for` node from the README: a 4B model triggered memory-pressure kills on an 18 GB machine.)
- Why does the client retry 502/503/504 but not 401?

**Blast radius**

- If `call_local_llm()` changes signature, who breaks? (4 callers: three mining scripts plus `phrase_profile()`. The orchestrator uses the same *endpoint* through its own client; see [Q3/Q4](queries.md).)
- If the serving profile changes from L40S to A100, what in the app depends on that name?

**Cross-repo**

- How does repo B get called from repo A?
- Are there duplicated mechanisms across repos? (Both repos implement retry with backoff: `call_local_llm()` and `chat_completion_with_retry()`.)

## Questions the graph *cannot* answer directly

| Question | Why the graph is silent |
|---|---|
| Which endpoint does the app hit at runtime? | The URL is a string default in `os.environ.get(...)`, not an edge |
| What data is in the SQLite DB? | `.db` and `.csv` files are not extracted |
| Is the batch job enabled in production? | It's gated by an env flag (`AI_MINING_ENABLED=1`), which is runtime state |
| Do client timeout and server startup timeout match? | Two constants in two repos, kept in sync only by comments |

These gaps are where the [case study](case-study.md) starts.

!!! tip "Expand vocabulary first"
    `query` matches your words against node labels. "LLM client" may find nothing while `call_local_llm` finds everything. Look up the graph's own terms (node labels, community names) before concluding something is missing.
