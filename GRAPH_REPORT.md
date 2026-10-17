# Hermes Agent — Live SQL Knowledge Graph Report (`GRAPH_REPORT.md`)

> **Axiom 1 & 7**: *Stop storing static notes; compile them live. Repos are not your brain; they are the compiler!*

## 1. Graph Telemetry Summary
- **SQLite WAL + FTS5 Database**: `/home/zen/.hermes/knowledge_compiler.db`
- **Python Files Compiled**: `3,521` across `agent/`, `tools/`, `tests/`, `.agents/skills/`
- **Total Knowledge Nodes**: `82,696`
- **Total Knowledge Edges**: `398,799`
- **Total AST Logic Trees (`CONTROL_FLOW` + `CALL_GRAPH`)**: `7,318`
- **JEV + Clef Evaluation**: Engine=`LOCAL_JEV`, Complexity=`0.0`, Output Tokens=`0`

## 2. Node Distribution by Type
| Node Type | Count |
|---|---|
| `FUNCTION` | `68,185` |
| `CLASS` | `9,737` |
| `FILE` | `3,521` |
| `MODULE` | `1,253` |

## 3. Edge Distribution by Provenance Relation (`EXTRACTED` vs `INFERRED`)
| Edge Type | Relation | Count |
|---|---|---|
| `CALLS` | `EXTRACTED` | `305,731` |
| `CONTAINS` | `EXTRACTED` | `68,148` |
| `IMPORTS` | `EXTRACTED` | `24,920` |
