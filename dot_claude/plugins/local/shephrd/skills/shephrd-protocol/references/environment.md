# Pane environment

A pane carries five variables. Two groups, by who writes them.

## Set by /spawn-agent

Passed as `--env` at split time, so the pane holds them before its first turn.

| Variable | Value | Why it cannot be derived later |
|---|---|---|
| `HERDR_AGENT_NAME` | the name passed to `-n` | herdr holds a name per pane and Claude registers its own; a pane reading only one of them can disagree with what peers address |
| `HERDR_AGENT_ROOT` | the directory the pane was opened for | `cwd` moves as the session works, and the directory it was spawned for does not |
| `HERDR_AGENT_MASTER` | the name of the session that spawned it | nothing in `herdr agent list` records who a pane answers to |

`herdr agent list` carries a `workspace_id` per pane and no field naming a master: measured on
2026-09-22 across six agents in three workspaces. Deriving the master from the workspace fails on
the same reading, where one workspace's first pane carried no `name` at all and another pane's
registered name disagreed with the title its terminal still displayed.

## Supplied by herdr

`HERDR_PANE_ID`, `HERDR_TAB_ID` and `HERDR_WORKSPACE_ID` arrive without being set. A pane reads
its own `HERDR_PANE_ID` and finds its record in `herdr agent list`, which carries the workspace,
the working directory and the name herdr knows.

Verified on 2026-09-22, splitting the bottom pane of a three-pane workspace: the first pane kept
its width of 128 columns while the bottom one went from 28 rows to two of 14, and the new pane
read back all five variables.

## Empty values

An empty `HERDR_PANE_ID` means the session is not running in a herdr pane at all. There is no
workspace to spawn into and no layout to read.

An empty `HERDR_AGENT_NAME` means the pane was opened by hand rather than by `/spawn-agent`.
Measured on 2026-09-22: the first pane of a workspace answered to `os-master` in `ListAgents`
with `HERDR_AGENT_NAME` unset. A session spawning from there resolves its own name from
`ListAgents` instead, since passing the empty value through would tell every sheep it has no
master.

An empty `HERDR_AGENT_MASTER` means the session coordinates itself. In a pane known to have been
spawned it means the pane predates this plugin, which is reported rather than treated as the
master role.
