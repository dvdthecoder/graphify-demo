# 3. Default vs deep mode (measured)

```bash
/graphify <path>               # default
/graphify <path> --mode deep   # deep
```

## What deep mode actually changes

Deep mode changes **one paragraph in the semantic extraction prompt**:

> be aggressive with INFERRED edges - indirect deps, shared assumptions, latent couplings. Mark uncertain ones AMBIGUOUS instead of omitting.

That's the whole difference. It doesn't change:

- the AST pass (code is still parsed the same way),
- the clustering algorithm,
- the scope of extraction: each repo is still extracted **on its own**.

## The experiment

We rebuilt both repos with `--mode deep` in a scratch copy, so the default graphs stayed untouched. The AST pass was identical, so the useful comparison is **what the semantic pass added on top of AST**.

=== "modal_io_serve (1 doc: README)"

    | Semantic pass added | Default | Deep | Change |
    |---|---|---|---|
    | Nodes | 34 | 32 | -2 |
    | Edges | 44 | 62 | **+41%** |
    | INFERRED edges | 14 | 20 | **+43%** |
    | AMBIGUOUS edges | 1 | 1 | 0 |
    | Tokens | 80,003 | 76,197 | ~same |

=== "drone-okg (11 docs)"

    | Semantic pass added | Default | Deep | Change |
    |---|---|---|---|
    | Nodes | 160 | 100 | -38% |
    | Edges | 304 | 116 | -62% |
    | INFERRED edges | 75 | 15 | -80% |
    | AMBIGUOUS edges | 6 | 1 | -5 |
    | Tokens | 197,020 | 129,655 | -34% |

!!! info "Caveats on these numbers"
    - The default graphs were built earlier in the day. Their AST layer has 15 more code nodes than today's re-run (graphify upgrade or file changes), so the drone-okg row is approximate.
    - Token figures for the default runs come from graphify's `cost.json`. The deep figures are the total tokens the subagents used. They're close enough to compare cost, not exact.
    - We ran each mode **once**. We don't know how the default run split files into chunks.

## Reading the result honestly

- **On a small, prose-heavy repo, deep mode did what it promises.** It produced ~40% more edges and INFERRED links from the same README, at the same cost: new `conceptually_related_to` edges, `implements` links from GPU profiles to server classes, and a "cold start handling" hyperedge.
- **On a larger repo, one deep run produced *less* than one default run.** The deep extractor handled 11 docs (including a large HTML report) in one pass and was more selective. Variation between LLM runs, mostly how much each chunk gets, outweighed the mode flag.
- **Deep mode is a prompt hint.** It doesn't guarantee a superset of default mode. If you need stable numbers, run with smaller chunks or average several runs.

## The cross-repo question, in both modes

| | Default | Deep |
|---|---|---|
| Concept node naming the other repo inside drone-okg | `Qwen3-30B-A3B-Instruct-2507-FP8 hosted LLM`, `modal_io_serve (separate repo)` | `Model backend: Qwen3-30B-A3B FP8 on Modal via modal_io_serve` (rationale: *"model serving kept in separate repo because GPU provisioning/scale-to-zero is reusable infrastructure"*) |
| Direct drone-okg ↔ modal_io_serve edges after merge | **0** | **0** |

Both modes *read* the dependency in the docs, but neither *linked* it, because every extractor sees only one repo. A concept node in `drone-okg::` can't point at `modal_io_serve::` IDs it has never seen.

!!! success "What does find candidates: matching labels after the merge"
    Comparing node labels across the two namespaces (token overlap ≥ 0.4) on the **default** merged graph proposed 5 links, including:

    ```text
    0.67  "Qwen3-30B-A3B-Instruct-2507-FP8 hosted LLM"  <->  "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8"
    0.50  "modal_io_serve (separate repo)"              <->  "modal-io-serve"
    ```

    On the **deep** merged graph the same threshold found 0. Deep mode's longer, more descriptive labels lowered the overlap, and the best pair scored 0.36. Label matching works as a candidate generator, but it depends on how nodes are labelled, so review its suggestions instead of adding them automatically.

## Graph health: where dangling edges come from

The health check flagged **147 dangling-endpoint edges** in drone-okg (12 in modal_io_serve). All of them come from the **AST** pass: `calls` to library functions that have no node in the graph. **None** came from the semantic pass. Every ID the deep subagents produced resolved to a real node.

## When to use deep mode

| Use deep | Stick with default |
|---|---|
| Architecture lives in READMEs/design docs | Code-heavy repo with a few docs |
| You want hypotheses about hidden coupling to review | You want a stable, low-noise graph |
| Small corpus, where variance matters less | Large corpus, where you'd need several runs to trust differences |
