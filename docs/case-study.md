# 7. Case study: tracing across HTTP

**Question:** *How does `modal_io_serve` get called from `drone-okg`?*

## Step 1 - Ask the graph

```text
direct drone-okg <-> modal_io_serve edges: 0
shared external modules: dataclasses, json, os, subprocess, sys
```

The graph's honest answer is "no connection". Any `path` between the repos goes through `os` or `sys`, the false bridges from [section 4](merging.md).

## Step 2 - Use the graph as an index, not an oracle

The graph still narrows the search a lot. A search for nodes whose labels or docstrings mention `llm`, `openai`, `endpoint` or `vllm` turns up a cluster in one file:

```text
call_local_llm()          gem_insight_generator/mine_specs_llm.py L349
extract_and_verify()      gem_insight_generator/mine_specs_llm.py L404
"OpenAI-compatible request/response shape throughout -- works against a hosted..."   (rationale node)
```

That **rationale node** is the key: it comes from a docstring that names the other repo in prose. The AST doesn't connect the two repos, but the docs do.

## Step 3 - Read the 20 lines the graph pointed at

```python
# mine_specs_llm.py (excerpt)
LLM_API_URL = os.environ.get(
    "LLM_API_URL", "https://<workspace>--qwen3-serve-serve-l40s.<region>.modal.direct/v1/chat/completions"
)
MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8")

COLD_START_RETRY_DELAYS = [15, 30, 60, 120, 240]  # ~8 min headroom
REQUEST_TIMEOUT = 20 * 60  # matches Modal's own container startup_timeout
```

The default URL encodes the **app name** (`qwen3-serve`) and the **server class** (`serve-l40s`). Repo B's graph already has a node for that class: `ServeL40S` in `src/qwen3_serve.py`.

## Step 4 - The confirmed picture

```mermaid
flowchart LR
  A1["mine_specs_llm.extract_and_verify()"] --> C
  A2["mine_use_case_llm.extract_and_verify()"] --> C
  A3["mine_bid_category_llm.extract_and_verify()"] --> C
  A4["phrase_capability_explanations.phrase_profile()"] -. INFERRED 0.85 .-> C
  C["call_local_llm()"] == "calls_http (manual)" ==> S["ServeL40S (qwen3_serve.py)"]
  O["orchestrator.build_agent() (pydantic-ai OpenAIProvider)"] == "calls_http (manual)" ==> S
  S --> V["vLLM 0.27.1: Qwen3-30B-A3B FP8"]
```

Things the trace showed that the graph didn't:

- **Two HTTP clients, five call paths.** Four functions go through `call_local_llm()`: three mining scripts, plus the bid-review agent's Skill A3 (`phrase_profile()`), which is linked only by an INFERRED edge because of the `sys.path` import. A **second, independent client** in `orchestrator.build_agent()` builds a pydantic-ai `OpenAIProvider` from the same `LLM_API_URL` default. We first missed this one, and the API inventory in [section 6](queries.md#q4-does-the-live-agent-depend-on-the-gpu-service) caught it.
- **The coupling is operational.** Client `REQUEST_TIMEOUT = 20*60` mirrors server `startup_timeout=20*60`. The client's retry schedule exists because the server runs `min_containers=0`.
- **Retry logic is duplicated** across the repos: `call_local_llm()` and `chat_completion_with_retry()`. The orchestrator's client has neither, so its handling of a cold start depends on the pydantic-ai/OpenAI SDK defaults.
- **The agent depends on the service in two ways.** Its MCP *tools* read a pre-computed SQLite cache, which Skill A3 fills in batch, so an outage there only makes text plainer. Its *reasoning model* runs live on the same endpoint, so a cold start delays every conversation turn.

!!! failure "Correction we made along the way"
    Our first write-up said the agent "reads only the SQLite cache at query time". That was wrong. The graph had no edge from `build_agent()` to the service, and we generalised from what the graph showed. The fix came from grepping for every HTTP client in both repos. The graph then explained how each one is reached, but it didn't find them.

## Step 5 - Write the finding back into the graph

```python
d["links"].append({
    "source": "drone-okg::gem_insight_generator_mine_specs_llm_call_local_llm",
    "target": "modal_io_serve::src_qwen3_serve_servel40s",
    "relation": "calls_http",
    "confidence": "EXTRACTED", "confidence_score": 1.0,   # the URL is literally in code
    "_origin": "manual",
    "source_file": "gem_insight_generator/mine_specs_llm.py",
    "source_location": "L133-L137",
    "context": "LLM_API_URL default",
})
```

After that, path queries cross the boundary:

```text
$ graphify path "phrase_profile()" "ServeL40S" --graph cross-repo-graph.json
Shortest path (2 hops):
  phrase_profile() --calls [INFERRED]--> call_local_llm() --calls_http [EXTRACTED]--> ServeL40S
```

## Challenges this exposes, and how to handle them

| Challenge | Mitigation |
|---|---|
| HTTP/RPC/queue calls don't appear in the graph | Add typed edges (`calls_http`, `publishes_to`) from config defaults, OpenAPI specs, or env templates |
| Manual edges are lost on rebuild | Keep them in a small `cross_repo_edges.json` and re-apply after every `merge-graphs` (see [Playbook](playbook.md)) |
| Edge targets a deployment detail (`serve-l40s`) | Point at the *API contract node* as well as the concrete class, so a GPU switch doesn't stale the edge |
| `sys.path` / dynamic imports degrade to INFERRED | Treat INFERRED `calls` as a to-do list; fix the packaging or confirm the edge by hand |
| Shared stdlib nodes create fake paths | Exclude external-module nodes when computing cross-repo paths |
| Contract constants drift silently | Make them visible: one shared doc, or a test that compares client timeout to server config |
