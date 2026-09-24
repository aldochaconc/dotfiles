---
description: Open a sheep pane that answers to this session, split so the first pane stays widest, carrying its identity from the environment
argument-hint: sheep name, optionally a path to work in, optionally --kind <kind> (default claude)
allowed-tools: ["Bash", "Read", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Spawn a sheep

Read `${CLAUDE_PLUGIN_ROOT}/commands/spawning.md` and run its procedure with the `/spawn-sheep` row:

| Field | Value |
|---|---|
| role | `sheep` |
| name | the argument |
| kind | the value of `--kind`, `claude` when absent |
| `HERDR_REPORTS_TO` | this session's name |
| `CLAUDE_UNATTENDED` | `1` |
| first prompt | the task and the scope |

A sheep is opened by a shephrd for work inside that shephrd's tree. Before opening one, check the
sheep already open against the reuse test in `shephrd-protocol`: a task that passes it goes to
that sheep by `SendMessage`, and no pane is opened.

A sheep stays open when its work is done. `/kill-sheep` closes it, run on the shephrd's order or
the user's.
