---
description: Open a sheep pane that answers to this session, split so the first pane stays widest, carrying its identity from the environment
argument-hint: sheep name, optionally a path to work in
allowed-tools: ["Bash", "Read", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Spawn a sheep

Read `${CLAUDE_PLUGIN_ROOT}/commands/spawning.md` and run its procedure with the `/spawn-sheep` row:

| Field | Value |
|---|---|
| role | `sheep` |
| name | the argument |
| `HERDR_REPORTS_TO` | this session's name |
| `CLAUDE_UNATTENDED` | `1` |
| first prompt | the task and the scope |

A sheep is opened by a shephrd for work inside that shephrd's tree. `/kill-sheep` is how it ends
itself when the work is done.
