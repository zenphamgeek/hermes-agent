---
name: obsidian-session-compiler
description: Compile agent sessions into bidirectional Obsidian notes.
version: 1.0.0
author: ZENPHAM & Antigravity, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [knowledge-compiler, clef, jev, sqlite, ast, bitemporal]
    related_skills: [decision-ledger, obsidian, session-librarian]
---
# obsidian-session-compiler

Part of the **7-Repo AI Knowledge Compiler Blueprint** unified with **Local JEV (`LocalJEVEvaluator`)** and **Clef Cloud (`ClefSelfGate` / `ClefSentinel`)**.

## When to Use

- Executing `link_session_to_vault` within the Sovereign Knowledge Compiler pipeline (`tools/jev_clef_knowledge_compiler.py`).
- Compiling live repository ASTs, SQL schemas, bi-temporal ADRs, Obsidian session links, or isolated Git index commits without storing stale static notes.

## How to Run

Invoke via `terminal`:

```bash
.venv/bin/python3 -c "from tools.jev_clef_knowledge_compiler import KnowledgeCompilerDB, LocalJEVEvaluator; db = KnowledgeCompilerDB('~/.hermes/knowledge_compiler.db'); print(hasattr(db, 'link_session_to_vault'))"
```

## Verification

Run the Knowledge Compiler & JEV/Clef quality gate suite:

```bash
.venv/bin/pytest tests/test_jev_clef_knowledge_compiler.py -v
```
