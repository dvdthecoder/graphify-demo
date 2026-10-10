# 2. Building per-repo graphs

Each repo got its own graph first. Merging comes later ([section 4](merging.md)).

```bash
cd drone-okg && /graphify .          # inside Claude Code (or: graphify extract .)
cd modal_io_serve && /graphify .
```

Each run writes `graphify-out/` with `graph.json`, `graph.html`, `GRAPH_REPORT.md` and a cache.

## Two extraction engines

graphify splits the corpus by file type and runs two different extractors:

| | **Structural (AST)** | **Semantic (LLM)** |
|---|---|---|
| Runs on | Code files (`.py`, `.ts`, `.go`, ...) | Docs, papers, images (`.md`, `.pdf`, `.png`, ...) |
| Produces | `contains`, `imports`, `calls`, `method` | Concepts, `references`, `rationale_for`, `conceptually_related_to`, `semantically_similar_to`, hyperedges |
| Cost | Free and deterministic | Tokens (subagents of the host agent, or Gemini if a key is set) |
| Confidence | Mostly EXTRACTED | Mix of EXTRACTED / INFERRED / AMBIGUOUS |

!!! tip "No API key needed"
    A code-only corpus never calls an LLM. For docs, graphify uses the host agent (e.g. Claude Code subagents) or Gemini if `GEMINI_API_KEY` is set.

## What came out

| Repo | Files | Nodes | Edges | Communities | EXTRACTED | INFERRED | AMBIGUOUS | Semantic input tokens |
|---|---|---|---|---|---|---|---|---|
| drone-okg | 61 | 773 | 1,681 | 39 | 1,593 (95%) | 82 (5%) | 6 | 197,020 |
| modal_io_serve | 7 | 64 | 86 | 7 | 71 (83%) | 14 (16%) | 1 | 80,003 |

Top relations in drone-okg: `calls` 478, `references` 329, `contains` 301, `rationale_for` 225, `imports` 190.

The small serving repo has **three times the INFERRED share** of the pipeline repo. It is mostly a README describing infrastructure, so most of its edges come from the LLM interpreting prose, not from parsing code.

## The three confidence labels, concretely

### EXTRACTED: stated in the source

```text
extract_and_verify()  --calls [EXTRACTED 1.0]-->  call_local_llm()     (mine_use_case_llm.py)
```

`mine_use_case_llm.py` does `from mine_specs_llm import call_local_llm`, and both files sit in the same directory, so the AST resolves the import exactly.

### INFERRED: a reasonable guess, with a score

```text
phrase_profile()  --calls [INFERRED 0.85]-->  call_local_llm()     (phrase_capability_explanations.py)
```

This is the *same kind of call*. Here, though, the caller lives in `bid_review_agent/` and reaches `gem_insight_generator/` through a `sys.path.insert(...)` hack. The AST can't follow a runtime path change, so graphify matched the name and downgraded the edge to INFERRED.

!!! warning "Lesson"
    An INFERRED edge often doesn't mean "the LLM guessed". It means **static resolution failed here**. Clusters of INFERRED `calls` edges show you where the import structure is unusual, and those are usually the places where tracing gets hard.

INFERRED scores come from a fixed rubric: 0.95 direct structural evidence, 0.85 strong, 0.75 reasonable, 0.65 weak, 0.55 speculative.

### AMBIGUOUS: flagged for review, not dropped

Real examples from drone-okg:

```text
Tool: check_spec_completeness  --calls [AMBIGUOUS]-->  spec_completeness.py
Tool: check_demand_fit         --calls [AMBIGUOUS]-->  demand_fit.py
```

These come from the agent's *documentation*, which says an MCP tool "calls" a script. The doc names a tool and a file but no function, so the extractor kept the claim and marked it uncertain. AMBIGUOUS edges make a good review queue.

## Things that silently shape the graph

- **Unclassified files.** drone-okg had 11 files not represented at all (8 `.csv`, 2 extensionless, 1 `.db`). Data files are invisible, including the SQLite database that is the real hub of the system.
- **Rationale nodes.** 225 `rationale_for` edges in drone-okg come from docstrings and comments explaining *why*. These turned out to be the most useful nodes for the cross-repo question (see the [case study](case-study.md)).
- **Caching.** Re-runs reuse semantic results per file. Changing the extraction prompt (e.g. a graphify upgrade) invalidates them.
