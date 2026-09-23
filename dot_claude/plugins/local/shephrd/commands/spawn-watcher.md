---
description: Open a watcher pane for the god, carrying the context and the hierarchy and no task, split so the first pane stays widest
argument-hint: watcher name
allowed-tools: ["Bash", "Read", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Spawn a watcher

Read `${CLAUDE_PLUGIN_ROOT}/commands/spawning.md` and run its procedure with the `/spawn-watcher` row:

| Field | Value |
|---|---|
| role | `watcher` |
| name | the argument |
| `HERDR_REPORTS_TO` | the god's name, `god` |
| `CLAUDE_UNATTENDED` | `1` |
| first prompt | the context and the hierarchy, and no task |

The first prompt carries who the shephrds are, what tree each holds and what is already known.
It carries no task: a watcher with no errand is at rest, and does not investigate, measure or
record on its own initiative until the god sends one. `report-gate.py` lets a watcher end a turn
that ran no tool without a message, so a watcher at rest stays silent.

A watcher writes to a repository only when an errand assigns it, and the scope recorded at step 5
names the repository for that errand alone.
