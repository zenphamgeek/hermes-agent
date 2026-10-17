---
name: graphify-sql
description: Compile codebases into queryable SQLite knowledge graphs.
version: 1.0.0
author: ZENPHAM & Antigravity, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [knowledge-compiler, clef, jev, sqlite, ast, bitemporal]
    related_skills: [understand-ast, decision-ledger]
---
# graphify-sql

Part of the **7-Repo AI Knowledge Compiler Blueprint** unified with **Local JEV (`LocalJEVEvaluator`)** and **Clef Cloud (`ClefSelfGate` / `ClefSentinel`)**.

## When to Use

- Executing `compile_python_file` within the Sovereign Knowledge Compiler pipeline (`tools/jev_clef_knowledge_compiler.py`).
- Compiling live repository ASTs, SQL schemas, bi-temporal ADRs, Obsidian session links, or isolated Git index commits without storing stale static notes.

## How to Run

Invoke via `terminal`:

```bash
.venv/bin/python3 -c "from tools.jev_clef_knowledge_compiler import KnowledgeCompilerDB, LocalJEVEvaluator; db = KnowledgeCompilerDB('~/.hermes/knowledge_compiler.db'); print(hasattr(db, 'compile_python_file'))"
```

## Verification

Run the Knowledge Compiler & JEV/Clef quality gate suite:

```bash
.venv/bin/pytest tests/test_jev_clef_knowledge_compiler.py -v
```
