# 8. Communities

## What a community is

After building the graph, graphify runs **community detection**. It partitions nodes into groups that are densely connected inside and sparsely connected to each other. Each node gets a `community` id, and the report gives each community a **cohesion** score (internal edge density).

Communities answer "what are the natural modules of this system?" from the edges alone, regardless of how the folders are laid out.

## Naming them

Raw output is `Community 0 ... Community 45`. Naming is a human (or LLM) step: look at each group's highest-degree members and source files, and pick 2-5 words.

| id | Size | Top members | Name |
|---|---|---|---|
| 0 | 81 | architecture.md, product_brief.md, Skill A1/B1 | Bid Review Agent Design |
| 13 | 18 | mcp_server.py, check_spec_completeness(), find_comparable_bids() | Bid Review MCP Server |
| 19 | 11 | mine_specs_llm.py, call_local_llm(), extract_and_verify() | LLM Spec Mining |
| 25 | 9 | phrase_profile(), _verify_summary() | Capability Explanation Phrasing |
| 41 | 10 | profiles.py, PROFILES, l40s profile, max_model_len | GPU Serving Profiles |
| 43 | 10 | ServeL40S, ServeA10040GB, _vllm_cmd() | Qwen3 vLLM Servers |

All 46 names are in the [appendix](appendix.md).

## What communities told us

- **Repos separate cleanly.** No community mixes drone-okg and modal_io_serve nodes. That's correct for code structure, and it's also a sign that no edges cross the repo boundary.
- **Tests cluster with what they test.** "Quote Verification Tests", "Airframe Vocabulary Tests" and "Whitespace Normalization Tests" each sit beside the functions they cover. That gives you a quick test-coverage map.
- **Docs form their own large cluster.** Community 0 (81 nodes) is design docs. Prose-heavy material groups together and links to code through `references` and `rationale_for`.
- **The persistence layer splits up.** `db.py` (124 edges) ends up spread across "DB Core", "DB Query Layer" and "DB Upserts", plus several tiny two-node communities (communities 35-38).

!!! warning "Tiny communities are noise"
    A community of 2 nodes (a function plus its docstring rationale) isn't a module. The report hides "thin" communities by default. Don't spend effort naming them.

## Communities can't find cross-repo links

Community detection only regroups existing edges. With zero edges between the repos, no algorithm will put `call_local_llm()` and `ServeL40S` in the same community. Communities show the structure of the edges you have, so if an edge is missing, clustering won't recover it.

## A visualization gotcha

The generated `graph.html` labels only nodes whose degree is at least **15% of the maximum degree**. With `db.py` at 124 edges, only **20 of 832** nodes had visible labels, and the rest looked like unlabelled dots. Every node was in the file. The fix was to set a font size on every node after export. The graph library then hides labels that are too small on screen, so they appear as you zoom in (script in the [appendix](appendix.md)).

[Open the interactive merged graph](assets/cross-repo-graph.html){ .md-button }
