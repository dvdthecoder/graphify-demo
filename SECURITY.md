# Security

This repo is a static documentation site. It contains no credentials and no runnable services.

- **Redaction:** the tutorial is based on two private repos. Live endpoint URLs, workspace names and secret names appear only as `<placeholders>`.
- **CI:** every push and PR runs a gitleaks secret scan and a strict MkDocs build. Workflows use least-privilege permissions, and third-party actions are pinned by commit SHA.
- **Reporting:** to report something sensitive that slipped through, open a private security advisory on this repo (Security → Report a vulnerability) rather than a public issue.
