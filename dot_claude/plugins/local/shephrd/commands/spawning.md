---
description: Shared procedure read by /spawn-sheep and /spawn-shephrd; not invoked alone, since it carries no role
disable-model-invocation: true
---

# Spawning a pane

`/spawn-sheep` and `/spawn-shephrd` open a pane by one procedure and differ
only in what they record. The procedure lives here once, and each command names its row of the
table below and sends its first prompt.

It sits in `commands/`, so Claude Code registers it as `/shephrd:spawning`. Run alone it has no
row to apply and would open a pane with no role, which is why the model never invokes it and a
person reaches for one of the two commands instead.

A pane opened by hand has to be told what it is afterwards, and a session restarted later comes
back under a generated name. Both are identity written after the fact instead of carried from
the start. `herdr pane split --env` sets variables on the launched process, and `HERDR_PANE_ID`
arrives on its own, so a pane knows its name, its workspace and its working directory before its
first turn.

## Roles

| Command | Role | Name | `HERDR_REPORTS_TO` | `CLAUDE_UNATTENDED` | First prompt |
|---|---|---|---|---|---|
| `/spawn-sheep` | `sheep` | the argument | this session's name | `1` | the task and the scope |
| `/spawn-shephrd` | `shephrd` | the bare name of the tree | the god's name | unset | the tree, the work and who it reports to |

This session's name comes from `HERDR_AGENT_NAME`, and from this session's entry in `ListAgents`
when that is empty, which is the case for any pane opened by hand. The god's name is `god`, which
`/shephrd` gives it when the user declares one, and it is verified in `ListAgents` before the
split. A spawn that resolves no recipient stops rather than opening a pane answering to nobody.

A shephrd takes the bare name of its tree, the name `/shephrd` would give it, so peers address a
shephrd by its tree whichever way it was opened.

The first prompt opens with the skills the pane loads before anything else:

| Skill | Loaded by |
|---|---|
| `shephrd:shephrd-protocol` | every pane: it is how the pane learns who it answers to |
| `skill-growth` | every pane: its trigger is a human correction, which in a pane is the user typing into it |
| `writing` | a pane whose task writes a doc, a skill, a commit or pull request body, or a tracker item |
| the skills the task names | the spawner lists them by name |

Nothing else is loaded up front. A skill that might apply triggers from its own description when
it does, and a pane that loads every candidate spends its context before the task starts.

`CLAUDE_UNATTENDED` stays off a shephrd because a shephrd reaches the user and a prompt in its
pane is answerable. `skills/shephrd-protocol/references/environment.md` holds what the variable
changes and why a hook needs it.

## Layout

The first pane of a workspace stays widest and is never split again: it holds the conversation,
and a column that keeps shrinking is unreadable. Every later pane splits the bottom of the right
column.

| Panes after | Split |
|---|---|
| 2 | `--direction right --ratio 0.59` on the first pane |
| 3 or more | `--direction down --ratio 0.5` on the bottom pane of the right column |

`herdr pane layout` gives every pane's rectangle. The right column is the set of panes whose `x`
is greater than the first pane's, and its bottom pane is the one with the largest `y` among
them. One pane leaves the second rule nothing to read, which is why the first row exists.

A ratio of 0.59 on the first split is what the hand-built layout measured, leaving the first
pane about three fifths of the width.

## Procedure

1. **Read the layout of this session's own workspace.**
   `herdr pane layout --pane "$HERDR_PANE_ID"` gives the pane count, each rectangle and the
   `workspace_id`. The pane to split and the direction follow from the table above.

   Without `--pane`, `herdr pane layout` returns the layout of the focused workspace, which is
   whichever one the user is looking at. Measured: a session in one workspace read back the
   three panes of another. A spawn computed from that layout opens in the wrong workspace or
   fails.

   An empty `HERDR_PANE_ID` means the session is not running in a herdr pane, and there is no
   workspace to spawn into: the command stops and says so.

2. **Split.** `herdr pane split <target> --direction <dir> --ratio <r> --cwd <path> --no-focus`
   plus one `--env` per variable in Environment below. `--no-focus` keeps the conversation where
   it is; a spawn that steals focus interrupts the person who asked for it.

   `<target>` is always written out. A split without it falls back to the focused pane, which
   can sit in another workspace, the same defect as step 1.

   Without `--cwd` the new pane inherits the current working directory, which is right when the
   pane works the same repository and wrong otherwise. A shephrd's `--cwd` is its tree.

3. **Start the agent with its name.** `herdr agent start <name> --kind <kind> --pane <pane> --
   <start>`, with `<start>` from the Agents table below. `<kind>` is `claude` unless
   `/spawn-sheep` names another; a shephrd is always `claude`, since it answers through
   `SendMessage` and `ListAgents`, which only a Claude Code session has.

   A start that fails leaves the pane from step 2 empty. It is closed with `herdr pane close
   <pane>` and the spawn reports the kind as failed, since the launch path of every kind but
   `claude` is not verified.

   The permission mode is set at launch and is not stored in settings, so a pane started without
   the flag comes up asking. What it asks about includes messages from other sessions: a pane in
   the default mode holds them for the user to approve, and they expire unanswered. Measured
   after four panes were restarted without it: three peer messages were lost, one refused and
   two expired. The hooks still run in this mode, since a hook decides on its own rather than
   through the permission layer.

   The `-n` is what `ListAgents` reports and what `SendMessage` addresses. Without it Claude
   builds a name from the basename of the working directory, and peers cannot address the pane
   by the name intended for it. `/restart-agents` carries the same rule and the failures behind
   it.

4. **Declare what it may touch, before it exists.**

   A directory is not a boundary. Four panes sat on one repository and three were nested inside
   each other, with nothing saying which files belonged to which; no conflict happened because
   only one of them wrote.

   The boundary is stated in the first prompt and recorded with the pane. Three parts:

   | Part | What it says | Why it is not the directory |
   |---|---|---|
   | paths | the files or subtrees this pane owns | a repository holds many, and two panes in one repository are ordinary |
   | branch | the branch it commits on, or none | two panes on one branch rewrite each other's history |
   | out of scope | what it must hand back rather than fix | a pane that repairs what it notices crosses into another's work |

   The third part stops the overlap that matters. A pane finding a defect outside its paths
   reports it to the session above, which routes it;
   `skills/shephrd-protocol/references/not-stalling.md` holds that rule and this is where the
   pane learns it applies to itself.

   Two panes overlap only when the session above says so, and then it names which one writes.
   Reviewing and building the same files is the ordinary case, and it works because one of them
   is read-only.

   A shephrd's scope is its tree.

5. **Record the identity outside the process.**
   `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/panes.py --write <pane> <name> <reports-to> <scope>
   --role <role>`, with the role from the table above. A sheep opened by the god adds
   `--autoreport false`: it reports only what other sessions have to learn, so `report-gate.py`
   does not hold its turns (`shephrd-protocol`, Reporting).

   The `--env` of step 2 lives in the pane's process, and a restart replaces that process:
   `herdr agent start` takes no `--env` and creates no pane. Measured: two panes restarted with
   their threads intact came back with both variables empty, and a sheep read as a shephrd. The
   registry survives that, and a session with an empty variable reads its own pane there before
   concluding it coordinates itself.

   The scope is what step 4 declared, written as the rest of the line, and no variable carries
   it: the registry is the only place it exists.

   `--role` is what the resolver trusts, and a record written without it falls back to deriving
   the role from the recipient. That derivation reads a shephrd reporting to the god as a sheep:
   pane `wA:p1` was recorded `shephrd` with the god above it, and every reader that derived
   called it a sheep.

6. **Label the pane.** `herdr pane rename <pane> <name>`, with the same name passed to `-n`.

   A pane with no label shows as a number in the sidebar, and so does a tab: measured, three
   tabs carried `label` equal to their index and two panes carried none. `/shephrd` offers
   stored panes by their label when it restores a workspace, so an unlabelled pane comes back
   identified only by its directory.

   This is a third name record, beside the two `/restart-agents` describes. It feeds the sidebar
   and `~/.config/herdr/session.json`; it is not what `SendMessage` addresses.

7. **Name the tab if it has none.** `herdr tab list` shows a `label` per tab, and a tab whose
   label is its own number was never named. `herdr tab rename <tab> <name>` takes the tree the
   workspace works on, which is the name the user reads in the sidebar. The god's workspace
   holds no tree, and its tab takes `god`: named after a tree, it came out as `machine` on
   2026-09-23.

   Only when it has none. A tab already named belongs to the workspace rather than to this
   spawn, and renaming it on every spawn would rename it after whichever pane opened last.

8. **Verify in `ListAgents`.** `herdr agent list` reads herdr's own record and says nothing
   about what peers see.

9. **Send the first prompt** from the table above, with `SendMessage` to the name verified in
   step 8.

## Agents

`herdr agent start` passes everything after `--` to the agent's binary, and each kind takes its
own arguments there. A running pane's kind is the `agent` field of `herdr agent list`, which is
where `/restart-agents` reads it.

| Kind | Start | Resume | Name the session | Skip permissions | Hooks of this plugin |
|---|---|---|---|---|---|
| `claude` | `-n <name> --dangerously-skip-permissions` | `-r <session_id> -n <name> --dangerously-skip-permissions` | `-n <name>` | `--dangerously-skip-permissions` | loaded |
| `codex` | `--dangerously-bypass-approvals-and-sandbox` | none | none | `--dangerously-bypass-approvals-and-sandbox` | none |
| any other kind `herdr` accepts | not verified | not verified | not verified | not verified | none |

The `claude` row comes from `claude --help`, and the `codex` flags from `codex --help` on
codex-cli 0.156.1. `codex resume <SESSION_ID>` exists, but a Codex pane writes no beat to read
the id from, so its resume cell is empty. not verified: a pane started with `--kind codex`
through `herdr agent start`.

A missing cell changes the procedure rather than the command:

| Missing | What happens |
|---|---|
| start | the kind is not spawned: the command stops and names it, since an invented flag fails in a pane nobody watches |
| name | the pane is reached with `herdr agent prompt` and `herdr agent read`; step 9 sends the first prompt that way, and step 8 checks `herdr agent list` |
| resume | a restart starts the pane fresh, and the report says so |
| hooks | the pane is ungated: `ask-gate.py`, `report-gate.py` and `canary.py` do not run in it, no beat is written, and silence from it is not read as a report |

## Environment

Set at split time with one `--env` each, so the pane carries them before its first turn:
`HERDR_AGENT_NAME`, `HERDR_AGENT_ROOT`, `HERDR_REPORTS_TO`, and `CLAUDE_UNATTENDED` where the
table above sets it.

Setting `HERDR_REPORTS_TO` puts a sheep in unattended mode with no command sent to
it: the pane asks the session above rather than the user from its first turn.

`skills/shephrd-protocol/references/environment.md` holds what each variable means and the
measurements behind them.

## Scope

The pane opens in the current workspace. A pane for another workspace is asked for by message to
a session already running there.

No name is reused. `herdr agent start` fails with `agent_name_taken` while herdr still holds a
record under that name, including one whose agent has exited.
