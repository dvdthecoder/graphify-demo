# 4. Merging repos

```bash
graphify merge-graphs \
  drone-okg/graphify-out/graph.json \
  modal_io_serve/graphify-out/graph.json \
  --out cross-repo-graph.json
```

## What the merge does

1. **Namespaces every node** as `<repo>::<local_id>`, e.g. `drone-okg::gem_insight_generator_mine_specs_llm_call_local_llm`. Each node also gets `repo` and `local_id` attributes.
2. **Shares external modules.** Nodes for third-party/stdlib imports (`os`, `sys`, `json`, `subprocess`, `dataclasses`, ...) live in their own namespace, so both repos point at the *same* `os` node.
3. **Re-clusters** the combined graph from scratch.

| | drone-okg | modal_io_serve | Sum | Merged |
|---|---|---|---|---|
| Nodes | 773 | 64 | 837 | **832** |
| Edges | 1,681 | 86 | 1,767 | **1,767** |
| Communities | 39 | 7 | 46 | **46** (recomputed) |
| Hyperedges | 6 | 3 | 9 | 9 |

The 5 missing nodes are the external modules both repos import (`os`, `sys`, `json`, `dataclasses`, `subprocess`), now one node each.

## The "145 cross-repo edges" trap

A naive count of edges whose endpoints have different namespace prefixes gave **145**. Every one of them was an import of an external module:

```text
db.py              --imports-->       sqlite3
spec_completeness.py --imports-->     math
mcp_server.py      --imports_from-->  mcp_server_fastmcp
...
```

Counting only edges **between the two real repos** gives:

```text
direct drone-okg <-> modal_io_serve edges: 0
```

!!! danger "Lesson"
    Shared stdlib nodes act as **false bridges**. They make two unrelated repos look connected, and in an undirected graph they create short paths (`A.x -> os <- B.y`) that mean nothing. Filter external modules out before measuring cross-repo coupling, or `graphify path` results become noise.

```python
repo = lambda node_id: node_id.split("::")[0]
REAL = {"drone-okg", "modal_io_serve"}
real_cross = [e for e in links
              if {repo(e["source"]), repo(e["target"])} == REAL]
```

## What merging is good for anyway

- One HTML view and one query surface for both codebases.
- Communities that show each repo's internal structure side by side.
- A place to **add** the cross-repo edges you discover (see the [case study](case-study.md)). The merge gives you a namespaced graph you can annotate.
