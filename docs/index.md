# Multi-Repo Calling Patterns with graphify

A field report on turning two real repositories into one knowledge graph, and what the graph does and does not tell you about how they call each other.

The setup is extremely common: an **application repo** that does the business work, and a separate **inference-service repo** that hosts a model behind an HTTP API. The application calls the service. No import connects them, only a URL in an environment variable.

We built a [graphify](https://github.com/Graphify-Labs/graphify) graph for each repo, merged them, asked questions, and found where the graph went quiet. This site walks through that end to end, with the real numbers.

## What you will learn

| Section | Takeaway |
|---|---|
| [Introduction to graphify](graphify-intro.md) | What graphify is, install, inputs and outputs, commands, integrations, what open source vs Cloud gives you |
| [Problem statement](problem.md) | The two repos in canonical terms: a *consumer pipeline* and a *model-serving service* |
| [Building per-repo graphs](building.md) | AST vs semantic extraction, and what EXTRACTED / INFERRED / AMBIGUOUS really mean |
| [Default vs deep mode](deep-mode.md) | Measured: what `--mode deep` adds on the same corpus |
| [Merging repos](merging.md) | `repo::` namespacing, deduped nodes, and why "145 cross-repo edges" meant zero |
| [Questions you can ask](questions.md) | `query`, `path`, `explain`, and the kinds of questions each answers |
| [Worked queries](queries.md) | Real answers to "which API calls exist?", traces, blast radius, and where the graph fails |
| [Case study](case-study.md) | Tracing "does the app actually use the service?" across an HTTP boundary |
| [Communities](communities.md) | What clusters are, how to name them, and when they are noise |
| [Playbook](playbook.md) | A checklist for making multi-repo graphs actually useful |
| [Visual walkthrough](walkthrough.md) | Animated tour of communities and HTTP traces in the interactive graph |

## The five findings in one screen

1. **Calls across an HTTP boundary don't show up in the graph.** The merged graph had zero edges between the two repos, even though two separate HTTP clients in the app (batch mining and the live agent) depend on the service.
2. **The "cross-repo" edges were all false positives.** All 145 of them pointed to shared stdlib modules (`os`, `sys`, `json`, ...).
3. **INFERRED edges mark places where resolution failed, even inside one repo.** A `sys.path` import hack turned a real call into a 0.85-confidence guess.
4. **Communities organise the code well but say nothing about runtime.** They grouped the serving code and the pipeline code cleanly, but clustering can't link two components that have no edge between them.
5. **The fix is cheap and partly manual.** Read config defaults, add a typed `calls_http` edge, record it in a small file so a rebuild doesn't lose it, and reach for deep mode only where docs carry the contract.

!!! note "Redaction"
    Repo names and code shapes are real. Live endpoint URLs, workspace names and secret names are masked as `<placeholders>`.
