# 9. Playbook: effective multi-repo graphs

A checklist distilled from this exercise.

## Before building

1. **Graph each repo separately first.** Per-repo graphs are cheaper to update (`--update` re-extracts only changed files) and easier to read.
2. **Put the contract in prose.** The cross-repo link in this study came from a docstring that named the other service. A short `INTEGRATIONS.md` per repo ("we call X at `$LLM_API_URL`, OpenAI shape, 20-minute timeout") gives semantic extraction something to work with.
3. **Make data visible if it matters.** `.db`/`.csv` files are skipped. If the schema is central, keep a `schema.md` or rely on the `CREATE TABLE` strings in code.

## Building

4. **Default mode for code-heavy repos.** AST does most of the work, and semantic extraction only touches docs.
5. **Deep mode where the docs carry architecture.** See the [measured comparison](deep-mode.md). It adds INFERRED edges from prose but can't see HTTP calls written only in code.
6. **Review AMBIGUOUS and low-score INFERRED edges.** Treat them as a queue: each one is either a missing import resolution or a doc claim that needs a real target.

## Merging

7. **Merge with `graphify merge-graphs`** into a separate file, and query it with `--graph`, so per-repo graphs stay intact.
8. **Filter external-module nodes** before counting or pathing across repos.
9. **Keep a cross-repo edge register** and re-apply it after every merge:

```json
// cross_repo_edges.json
[
  {"source": "drone-okg::gem_insight_generator_mine_specs_llm_call_local_llm",
   "target": "modal_io_serve::src_qwen3_serve_servel40s",
   "relation": "calls_http", "confidence": "EXTRACTED", "confidence_score": 1.0,
   "evidence": "mine_specs_llm.py L133-137: LLM_API_URL default"}
]
```

```python
import json
g = json.load(open("cross-repo-graph.json"))
ids = {n["id"] for n in g["nodes"]}
for e in json.load(open("cross_repo_edges.json")):
    assert e["source"] in ids and e["target"] in ids, f"stale edge: {e}"   # catches renames
    g["links"].append({**e, "_origin": "manual", "weight": 1.0})
json.dump(g, open("cross-repo-graph.json", "w"), indent=2)
```

The `assert` matters. If a refactor renames `ServeL40S`, the register fails loudly instead of the edge disappearing without anyone noticing.

## Finding cross-repo edges semi-automatically

Grep both repos for the strings that indicate a network boundary:

```bash
grep -rnE "os\.environ\.get\(\"[A-Z_]*(URL|HOST|ENDPOINT)" repo-a/
grep -rnE "@app\.(get|post)|@modal\.web_server|FastAPI\(" repo-b/
```

Match client URL defaults to server route and app names, then add one edge per match.

## Querying

10. Start with `query` for orientation, use `path` to test a hypothesis, and use `explain` for a single node.
11. When the graph says "no connection", search **rationale nodes** next. Comments and docstrings often name the other system.
12. Name the communities. It takes a few minutes, and every later report and query reads better for it.

## Visualizing

13. Above roughly 5,000 nodes graphify switches to an aggregated community view. Below that, check that labels are visible (see [Communities](communities.md#a-visualization-gotcha)).
