---
description: Open a shephrd pane on a tree, reporting to the god, split so the first pane stays widest
argument-hint: path of the tree, optionally what the shephrd works on
allowed-tools: ["Bash", "Read", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Spawn a shephrd

Read `${CLAUDE_PLUGIN_ROOT}/commands/spawning.md` and run its procedure with the `/spawn-shephrd` row:

| Field | Value |
|---|---|
| role | `shephrd` |
| name | the bare name of the tree |
| `--cwd` | the tree |
| `HERDR_REPORTS_TO` | the god's name, `god` |
| `CLAUDE_UNATTENDED` | unset |
| first prompt | the tree, the work and who it reports to |

The god opens shephrds, one per tree. A god that is not in `ListAgents` leaves the shephrd
nobody to report to, and the spawn stops and says so.
