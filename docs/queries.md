# 6. Worked queries: API calls and traces

Real questions, real graphify output (lightly trimmed), and the answer checked against the source code. Every query ran on the merged graph (832 nodes) with the two manual `calls_http` edges added.

!!! warning "Gotcha: `--graph` and query/explain"
    In the graphify version used here, `path` honours `--graph` **only when the flag comes last**. `query` and `explain` ignored it and silently read `./graphify-out/graph.json`. The output header says which graph was loaded (`Graph: graphify-out/graph.json (804 nodes)`), so **always check the node count in the header**. Our workaround was a scratch directory whose `graphify-out/graph.json` is the merged graph:

    ```bash
    mkdir -p q/graphify-out && cp cross-repo-graph.json q/graphify-out/graph.json && cd q
    graphify query "..."
    ```

---

## Q1. Which API calls does the system make, and which does it expose?

**Ground truth from the code.** We grepped both repos for `requests.*`, `urllib`, `OpenAI(`, `base_url` and routes:

| Direction | Caller (repo A unless noted) | Target | Mechanism |
|---|---|---|---|
| Outbound | `common.fetch_csrf_token()` | GeM portal `GET /all-bids` | `requests.Session` |
| Outbound | `common.post_search()` → `search_all_pages()` | GeM portal `POST /all-bids-data` | `requests.Session` |
| Outbound | `harvest_documents.download()` | GeM `GET /showbidDocument/<id>` + GTC PDFs | `requests.Session` |
| Outbound | `mine_specs_llm.call_local_llm()` | Repo B `POST /v1/chat/completions` (L40S) | `requests.post(LLM_API_URL)` |
| Outbound | `orchestrator.build_agent()` | Repo B `/v1` (same endpoint) | pydantic-ai `OpenAIProvider(base_url=...)` |
| Inbound (B) | `ServeL40S`, `ServeA10040GB` | `/v1/chat/completions`, `/v1/models` | vLLM OpenAI server |
| Inbound (B) | `ServeT4` (Laya) | `POST /v1/systemone` | laya-serve |
| Test (B) | `scripts/test_client.py`, `scripts/test_laya.py` | the two inbound APIs | `OpenAI(...)`, `urllib.request` |

**What the graph says.**

```text
$ graphify query "which outbound http api calls does the pipeline make"
Graph: graphify-out/graph.json (832 nodes) | Start: ['Pipeline', 'OpenAI-compatible HTTP API', 'make_bid_record()'] | 17 nodes found
NODE fetch_csrf_token()   [src=gem_insight_generator/common.py loc=L67  community=Document Harvesting]
NODE search_all_pages()   [src=gem_insight_generator/common.py loc=L129 community=Document Harvesting]
EDGE main() --calls [EXTRACTED]--> fetch_csrf_token()  at=gem_insight_generator/scraper.py:L157
EDGE main() --calls [EXTRACTED]--> search_all_pages()  at=gem_insight_generator/scraper.py:L171
...
```

**Verdict: partial.** The query found the GeM scraping chain, because those functions are named after what they do. It missed both LLM clients and the document downloader. The graph has no "external service" nodes: a URL string is not a node, so "API call" is something you have to infer from function names and `Session` references.

!!! tip "Take-away"
    For an API inventory, **grep first, graph second**. Grep finds the call sites, and the graph shows how each one is reached (Q2, Q3).

---

## Q2. Trace an LLM call from the app to the GPU

```text
$ graphify path "phrase_profile()" "ServeL40S" --graph cross-repo-graph.json
Shortest path (2 hops):
  phrase_profile() --calls [INFERRED]--> call_local_llm() --calls_http [EXTRACTED]--> ServeL40S

$ graphify path "build_agent()" "ServeL40S" --graph cross-repo-graph.json
Shortest path (1 hops):
  build_agent() --calls_http [EXTRACTED]--> ServeL40S
```

**Verdict: works, but only because of the manual edges.** Without them, both commands report no path.

---

## Q3. Blast radius: who breaks if `call_local_llm()` changes?

```text
$ graphify explain "call_local_llm()"
Node: call_local_llm()   Community: LLM Spec Mining   Degree: 9
  <-- extract_and_verify() [calls] [EXTRACTED]  mine_specs_llm.py:L409
  <-- extract_and_verify() [calls] [EXTRACTED]  mine_bid_category_llm.py:L161
  <-- extract_and_verify() [calls] [EXTRACTED]  mine_use_case_llm.py:L119
  <-- phrase_profile()     [calls] [INFERRED]   phrase_capability_explanations.py:L168
  --> ServeL40S            [calls_http] [EXTRACTED]  mine_specs_llm.py:L133-L137
```

**Verdict: correct and complete for Python callers**, with exact file:line for each. The INFERRED caller is the `sys.path` import discussed in [section 2](building.md). Note what it does **not** include: `orchestrator.build_agent()` shares the endpoint but not this function, so changing the *function* doesn't affect the agent, while changing the *endpoint* affects both.

---

## Q4. Does the live agent depend on the GPU service?

```text
$ graphify explain "build_agent()"            # before the manual edge
Node: build_agent()   Community: Pydantic AI Orchestrator   Degree: 3
  <-- orchestrator.py        [contains]
  <-- _run_scripted_loop()   [calls]
  --> Agent                  [references]
```

**Verdict: the graph misses it.** `build_agent()` builds `OpenAIProvider(base_url=_BASE_URL)` from the *same* `LLM_API_URL` default as the mining scripts. A comment says it is "a second caller of the one already-proven endpoint". The graph sees a reference to `Agent` and nothing else.

This changed our own earlier conclusion. We had said the agent only reads a pre-computed SQLite cache. That holds for its MCP **tools**, but the agent's **reasoning model** runs on the same Modal endpoint. A cold start delays every live conversation turn, not just batch jobs.

---

## Q5. What does the agent's MCP server expose?

```text
$ graphify query "what does the mcp server expose and what does each tool call"
Start: ['server', 'tool', 'mcp_server.py', ...] | 5 nodes found
NODE server [community=Laya T4 Server]          <- wrong repo, matched on the word "server"
```

```text
$ graphify explain "mcp_server.py"
Node: mcp_server.py   Community: Bid Review MCP Server   Degree: 16
  --> get_capability_questions()      [contains]  L51
  --> explain_indigenous_capability() [contains]  L63
  --> check_spec_completeness()       [contains]  L76
  --> find_comparable_bids()          [contains]  L91
  --> parse_capability_description()  [contains]  L107
  --> check_demand_fit()              [contains]  L117
  --> db.py, spec_completeness.py, demand_fit.py, mvp.py, parse_capability_text.py [imports]
```

**Verdict:** the free-text `query` matched a generic word in the wrong repo, while `explain` on a known node gave the full answer: six tools and the five modules behind them. **Once you know a node name, use `explain`.**

---

## Q6. The false-bridge trap, live

```text
$ graphify path "orchestrator.py" "ServeL40S" --graph cross-repo-graph.json --undirected
Shortest path (3 hops):
  orchestrator.py --imports--> os <--imports-- qwen3_serve.py --contains--> ServeL40S
```

**Verdict: wrong, but it looks plausible.** Both files import `os`, so an undirected search treats `os` as a bridge. The path looks like an answer but carries no meaning. Always check whether a cross-repo path runs through a stdlib node ([section 4](merging.md)).

---

## Summary

| Question type | graphify alone | With grep + manual edges |
|---|---|---|
| API inventory | Partial (named functions only) | Complete |
| Trace in-process calls | Excellent, with file:line | n/a |
| Trace across HTTP | None, or false bridges | Correct |
| Blast radius of a function | Excellent | n/a |
| "What does X expose" | Good with `explain`, weak with free-text `query` | n/a |
