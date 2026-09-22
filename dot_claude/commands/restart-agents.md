---
description: Restart Claude in herdr panes so they pick up new permissions and hooks, keeping each session's name
argument-hint: pane ids or names, space separated; empty restarts every peer pane but this one
allowed-tools: ["Bash", "ListAgents", "AskUserQuestion"]
---

# Restart agent panes

A permission rule and a hook are read once, when a session starts. A session that has been
running since before they changed still holds the old ones, and only a restart replaces them.
An instructions file is different: it is reinjected each turn, so a rule written there is
already live everywhere and is not a reason to restart.

Restarting through `herdr` loses the session name unless the name is passed to the binary. The
procedure below keeps it. Every step was measured on 2026-09-22; the failures it avoids are
recorded with it.

## What the name is, and why two records disagree

`herdr` keeps a name per pane. Claude Code registers its own session name, which is what
`ListAgents` reports and what `SendMessage` addresses. They are separate records.

`claude -n <name>` sets the Claude side and the terminal title together. `herdr agent rename`
sets the `herdr` side alone: run by itself after a restart, the pane reads correct in
`herdr agent list` while peers still see a generated name such as `dotfiles-a2`. Both records
have to be written, which is why the procedure has a rename step even though `-n` is passed.

## Procedure

Per pane, in order. The target of each command is the pane id, which never changes.

1. **Read the pane before touching it.** `herdr agent read <pane>` shows an open approval
   dialog or half-typed text. Keys sent into either land in that context instead of the one
   expected, so a pane that is not at a clean prompt is reported and skipped.

2. **Ask the session what it loses.** A message asking for uncommitted work, anything running,
   and one line on what to resume. Its context dies with the process, so what is not written to
   disk is gone. A session that does not answer is reported to the user, who decides.

3. **Exit.** `herdr agent prompt <pane> "/exit"`. Confirmed when `herdr agent read <pane>`
   returns `agent_not_found`: the pane is now at its shell prompt, which is what step 4 needs.

   `herdr agent send-keys <pane> ctrl+d` does not close it. Measured: the call returns `ok` and
   the agent stays alive.

4. **Start with the name.** `herdr agent start <temp> --kind claude --pane <pane> -- -n <name>`.

   Everything after `--` goes to the `claude` binary, and `-n <name>` is what survives into
   `ListAgents`. `<temp>` names the `herdr` record and must differ from `<name>`: `herdr` still
   holds the record of the agent that just died, so reusing the real name fails with
   `agent_name_taken`. A pane id is not a legal value either: a name starts with a lowercase
   letter and carries lowercase letters, digits, `-` or `_`.

5. **Sync the `herdr` record.** `herdr agent rename <pane> <name>`.

6. **Verify in `ListAgents`, never in `herdr agent list`.** The second reads the `herdr` record,
   which step 5 just wrote and which tells nothing about what peers see. Only `ListAgents`
   answers whether the session can be addressed by name.

## Scope

A master restarts the panes of its own workspace. `herdr agent list` gives the `workspace_id`
of each pane; a pane in another workspace belongs to that workspace's master and is delegated by
message rather than restarted here.

This session never restarts itself: the process running the command is the one that would die.
The user restarts it, or it is left running and reported.

## Reporting

Per pane: its name, whether it answered step 2, and the name `ListAgents` reports at the end. A
pane skipped at step 1 is named with what was on screen. A pane whose name did not survive is
named with the generated one peers now have to use.
