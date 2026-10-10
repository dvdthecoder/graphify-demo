# Multi-Repo Calling Patterns with graphify

A tutorial site on using [graphify](https://github.com/Graphify-Labs/graphify) across two real repos that talk over HTTP: a consumer pipeline and a model-serving service.

The site covers:

- an introduction to graphify
- building per-repo graphs, and default vs deep mode (measured)
- merging graphs and the false-bridge trap
- worked queries: API call inventory, traces, blast radius
- tracing across an HTTP boundary
- communities
- a playbook
- an animated walkthrough of the interactive graph

## Run locally

```bash
pip install -r requirements.txt
mkdocs serve        # http://127.0.0.1:8000
```

## CI and deploy

`.github/workflows/docs.yml` runs a gitleaks secret scan and `mkdocs build --strict` on every push and PR. On `main` it deploys to GitHub Pages. In the repo settings, set **Pages > Source** to **GitHub Actions**.

## Layout

```
docs/                 pages (Markdown)
docs/assets/          interactive graph HTML (redacted) + walkthrough GIF
docs/scripts/         regen_html.py - labels communities, shows all node labels
mkdocs.yml            site config and nav
```
