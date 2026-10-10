# Appendix

## Command reference

```bash
# per-repo build (inside Claude Code)
/graphify .                      # default
/graphify . --mode deep          # aggressive INFERRED edges from docs
/graphify . --update             # re-extract only changed files

# headless / CI
graphify extract . [--mode deep] [--backend gemini|claude|...]

# merge
graphify merge-graphs a/graphify-out/graph.json b/graphify-out/graph.json --out cross-repo-graph.json

# query a non-default graph
graphify query "<question>" --graph cross-repo-graph.json [--dfs] [--budget 1500]
graphify path  "<A>" "<B>"  --graph cross-repo-graph.json
graphify explain "<node>"   --graph cross-repo-graph.json

# visualize
graphify export html --graph cross-repo-graph.json   # writes graph.html next to the JSON
```

## Regenerating the HTML with community names and full labels

[`scripts/regen_html.py`](scripts/regen_html.py) does three things:

1. writes `community_name` onto every node of the merged JSON,
2. calls graphify's `to_html()` with the names,
3. gives every node a label font size, so labels appear as you zoom in instead of being hidden below graphify's 15%-of-max-degree threshold.

```bash
$(cat graphify-out/.graphify_python) scripts/regen_html.py cross-repo-graph.json cross-repo-graph.html
```

## All 46 community names (merged graph)

| id | Name | id | Name |
|---|---|---|---|
| 0 | Bid Review Agent Design | 23 | Airframe Vocabulary Tests |
| 1 | DB Core & Spec Doc Shape | 24 | Capability Explanation Grouping |
| 2 | Report Sparklines | 25 | Capability Explanation Phrasing |
| 3 | Document Harvesting | 26 | Airframe Fallback Gate |
| 4 | Spec Dictionary & Tech Reqs | 27 | Component Taxonomy Ingest |
| 5 | Classify & Report Generation | 28 | Whitespace Normalization Tests |
| 6 | Line Item Parsing & Status | 29 | OpenWebUI Pipeline Wrapper |
| 7 | DB Query Layer | 30 | Keyword & Taxonomy Seeding |
| 8 | Pydantic AI Orchestrator | 31 | Bid Facts Mining |
| 9 | Demand Fit Analysis | 32 | Buyer Type Classifier |
| 10 | DB Upserts & Ingest | 33 | OCR Recovery |
| 11 | MVP Bid Resolution | 34 | Boilerplate Quote Tests |
| 12 | Spec Completeness Skill | 35 | Bid Classification Feed |
| 13 | Bid Review MCP Server | 36 | Component Demand Query |
| 14 | Platform & Weight Classifiers | 37 | Harvested Bid Lookup |
| 15 | Capability Text Parsing | 38 | Recent Pipeline Runs |
| 16 | Keyword Bid Scraping | 39 | Modal Serving Concepts |
| 17 | LLM Pipeline Stage 4 | 40 | Modal Smoke Tests |
| 18 | Line Item Use Case & Specs | 41 | GPU Serving Profiles |
| 19 | LLM Spec Mining | 42 | Modal Apps & Secrets |
| 20 | Pipeline Run Tracking | 43 | Qwen3 vLLM Servers |
| 21 | VTOL Category Audit | 44 | Laya T4 Server |
| 22 | Quote Verification Tests | 45 | modal-io-serve Package |

Communities 0-38 are drone-okg and 39-45 are modal_io_serve. No community contains nodes from both repos.

## Numbers at a glance

| Graph | Nodes | Edges | Communities |
|---|---|---|---|
| drone-okg (default) | 773 | 1,681 | 39 |
| modal_io_serve (default) | 64 | 86 | 7 |
| Merged (default) | 832 | 1,767 | 46 |
| Merged + 2 manual `calls_http` edges | 832 | 1,769 | 46 |
| drone-okg (deep) | 713 | 1,493 | 39 |
| modal_io_serve (deep) | 62 | 104 | 10 |
| Merged (deep) | 770 | 1,597 | n/a |
