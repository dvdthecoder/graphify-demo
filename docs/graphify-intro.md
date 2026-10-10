# 0. Introduction to graphify

[graphify](https://github.com/Graphify-Labs/graphify) turns a project into a **knowledge graph** that you and your AI coding assistant can query instead of grepping through files one by one. The project describes itself as *"local deterministic AST parsing, every edge explained, no vector store."*

- **Repo:** [github.com/Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) (maintained by Graphify Labs)
- **Docs:** [docs.graphify.com](https://docs.graphify.com)
- **Package:** `graphifyy` on PyPI (two y's). The command is `graphify`.
- **License:** the repo ships Apache-2.0 and MIT license files.
- **Version used in this tutorial:** `graphify 0.9.67`

!!! warning "Name confusion"
    Several unrelated `graphify*` packages exist on PyPI. Install **`graphifyy`**.

## Why a graph instead of search or embeddings?

| Approach | What you get | What you lose |
|---|---|---|
| `grep` / file search | Exact matches | Structure: who calls whom, what belongs together |
| Vector RAG | Fuzzy semantic recall | Explainability: *why* is this chunk relevant? |
| **graphify** | Nodes and typed edges (`calls`, `imports`, `references`, `rationale_for`, ...), each with a source location and a confidence label | Anything static analysis and doc extraction can't see (e.g. [HTTP calls between repos](case-study.md)) |

The graph is traversed, not embedded. Every answer is a set of nodes and edges that you can check against `file:line`.

## Install

```bash
uv tool install graphifyy          # or: pipx install graphifyy / pip install graphifyy
graphify install                   # register the skill with your AI assistant
graphify install --project         # ...or only for this repo
```

Python 3.10+. Optional extras use the form `uv tool install "graphifyy[pdf,mcp,neo4j]"`:

- **Inputs:** `pdf`, `office`, `google`, `video`, `sql`, `postgres`
- **Outputs and integrations:** `mcp`, `neo4j`, `falkordb`, `svg`, `leiden`
- **LLM backends:** `ollama`, `openai`, `gemini`, `anthropic`, `bedrock`
- **Extra languages:** e.g. `terraform`, `ocaml`
- **Everything:** `all`

## What it reads

| Input | How | Needs an LLM? |
|---|---|---|
| Code (~40 languages via tree-sitter) | Deterministic AST pass | **No.** Local and free |
| Markdown, text, PDFs, Office docs, images | Semantic extraction | Yes: your assistant's model, or an API key |
| SQL schemas, live PostgreSQL (`--postgres DSN`) | Schema extraction | No |
| Video / audio | Local transcription (faster-whisper), then semantic | Yes, for the semantic step |

It respects `.gitignore`, `.graphifyignore` and `--exclude`. `--code-only` skips everything but code.

## What it produces

Everything goes into `graphify-out/`:

- **`graph.html`**: interactive, clickable graph, with a community legend, search and a node info panel ([see the walkthrough](walkthrough.md))
- **`GRAPH_REPORT.md`**: plain-language report with god nodes (most connected), surprising connections, communities and suggested questions
- **`graph.json`**: the full graph, ready for tools and GraphRAG

Each edge carries a **confidence label**:

- **EXTRACTED**: stated explicitly in the source.
- **INFERRED**: resolved by graphify or the extraction model, with a score.
- **AMBIGUOUS**: flagged for review. graphify's semantic extraction prompt uses it, and our graphs contained a handful of these edges ([section 2](building.md)).

Nodes are grouped into **communities** with Leiden clustering. You can tune it with `--resolution` and `--exclude-hubs` ([section 8](communities.md)). Comments such as `# WHY:` / `# NOTE:`, docstrings and ADR references become **rationale** nodes. These turned out to be the key to our [cross-repo trace](case-study.md).

## Everyday usage

Inside an AI assistant (Claude Code shown; Codex uses `$graphify`):

```text
/graphify .                                   # build the graph for this repo
/graphify ./docs --update                     # incremental: only changed files
/graphify . --cluster-only --resolution 1.5   # re-cluster only
/graphify . --mode deep                       # more aggressive INFERRED edges from docs
/graphify query "what connects auth to the database?"
/graphify path "UserService" "DatabasePool"
/graphify explain "RateLimiter"
/graphify add https://arxiv.org/abs/1706.03762
```

From a terminal or CI:

```bash
graphify extract . [--mode deep] [--backend gemini|claude|openai|ollama|...]
graphify merge-graphs a/graphify-out/graph.json b/graphify-out/graph.json --out merged.json
graphify export html|svg|wiki|callflow-html|neo4j|falkordb [--graph PATH]
graphify hook install                         # rebuild on commit
```

## Assistant integrations

The project lists 20+ platforms, including Claude Code, Cursor, Codex, Gemini CLI, GitHub Copilot CLI / VS Code Copilot Chat, Aider, OpenCode, Kilo Code, Kiro, Amp, Devin CLI and generic Agent Skills (`--platform agents`). On Claude Code, Gemini CLI and CodeBuddy, hooks steer the assistant to query the graph first. Elsewhere it uses instruction files (`AGENTS.md`, `.cursor/rules/graphify.mdc`). An **MCP stdio server** (`--mcp`) exposes the graph to any MCP client.

## LLMs and keys

- **Code-only corpus:** no API key, can run fully offline.
- **Docs, PDFs, images:** inside an assistant, the assistant itself does the extraction (in Claude Code, through subagents). Headless runs auto-detect a backend from environment keys in roughly this order: Gemini, Kimi, Claude, OpenAI, DeepSeek, Azure, Bedrock, then Ollama for fully local runs.
- **Privacy:** no telemetry. Queries are logged locally (`~/.cache/graphify-queries.log`). Set `GRAPHIFY_QUERY_LOG_DISABLE=1` to turn that off.

## Multi-repo: what open source gives you

The open-source CLI provides **`graphify merge-graphs`**, which namespaces each repo's nodes and combines them into one graph. That is what this tutorial uses. Continuous monorepo and cross-repo graphs are part of the paid **Graphify Cloud**, which we did not use.

The rest of this site shows what `merge-graphs` gives you on a real pair of repos, where it stops, and how to fill the gaps.

## Published benchmarks (project's own claims)

| Benchmark | Metric | graphify | Comparison |
|---|---|---|---|
| LOCOMO | recall@10 | 0.497 | mem0 0.048, supermemory 0.149 |
| LOCOMO | QA accuracy | 45.3% | supermemory 49.7% |
| LongMemEval-S | QA accuracy | 76% | ties dense RAG |
| ERPNext | key-fact coverage | 82.0% | grep baseline 70.8% |

These are the project's own numbers and we did not reproduce them. The headline "cut agent token spend by 80%" is stated for Graphify Cloud.

## Things we hit that the README doesn't mention

Found in this tutorial with `graphify 0.9.67`:

- **`--graph` handling:** `query` and `explain` ignored `--graph` and read `./graphify-out/graph.json`. `path` honours `--graph` only when the flag comes last ([details](queries.md)).
- **HTML labels:** `graph.html` labels only nodes with ≥15% of the max degree. In our graph that was 20 of 832 ([fix](communities.md#a-visualization-gotcha)).
- **Merged graphs:** shared stdlib nodes act as false bridges between repos ([section 4](merging.md)).
