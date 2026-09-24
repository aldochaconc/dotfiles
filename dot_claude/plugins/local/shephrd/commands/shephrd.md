---
description: Take the coordinating role for the tree this session sits in, resuming the previous session there or asking what this one is for
argument-hint: none; the working directory is what the command reads
allowed-tools: ["Bash", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Shepherd a tree

One session per tree coordinates it: it talks to the user, decides, and asks the other panes for
mechanical work. This command takes that role. It takes no arguments, reads the working
directory and what was left around it, and asks the user what the reading means.

Run once, right after opening a pane.

## Position

What the working directory governs is not a category. It is read, reported and then confirmed by
the user, because the same shape means different things in different places and no check
distinguishes them.

What can be read, and what each fact is evidence of:

| Read | Command | What it bears on |
|---|---|---|
| whether this directory is a repository | `git rev-parse --show-toplevel` | whether the session's own commits belong to this tree or to one below it |
| repositories below it | `find . -maxdepth 2 -name .git` | whether work here means opening panes on them |
| what a repository says about itself | its `CLAUDE.md`, its README | reach beyond the tree: what is deployed, applied or installed from it, which no filesystem check shows |
| what was worked here before | the transcripts under `~/.claude/projects` | whether the answer is already known and need not be asked |

That reading is reported as a reading, never as a verdict. A directory holding repositories and
none of its own may be a place to coordinate projects or just a folder someone made; a
repository with repositories nested inside may own them or merely contain them. The filesystem
cannot tell, so the report says what was found and the question below asks what it means.

The one case where the answer is on disk is the fourth row: a repository whose `CLAUDE.md`
states its own reach has already answered, and the session reads it instead of asking.

## Continuity

A tree that was worked before has a transcript directory under `~/.claude/projects`, named after
the absolute path with every `/` replaced by `-`. Its presence is the test. Measured: 57
transcripts for one directory, 7 for another.

The flattened name is not unique: `/a-b/c` and `/a/b-c` both become `-a-b-c`. A transcript is
offered only when the first `"cwd"` field in it equals this tree's absolute path; the field moves
later in the file when the session changes directory, so the first one is the one that names
where it started.

| Found | Action |
|---|---|
| a transcript for this directory | the user is offered the summary of what it was, and chooses to resume it or to start fresh |
| none | the tree is new to this machine and the session starts from the questions below |

Resuming is offered rather than taken. A transcript proves a session existed here and says
nothing about whether its thread is the one to continue, so what is shown is the summary from
the handoff, or the last exchange of the transcript when there is no handoff, and the choice is
the user's. Starting fresh on a tree that has a transcript is an ordinary answer, not a loss:
the transcript stays where it is.

The relaunch reads the pane's kind in `ListAgents` first: a session of kind `bg` is not closed by
`/exit`, which moves it to the background sessions panel (`references/herdr-cli.md`), and it is
reported rather than relaunched. An interactive one is replaced in place: `herdr agent prompt <pane> "/exit"`, wait for the
pane to leave `herdr agent list`, then `herdr agent start <temp> --kind claude --pane <pane> --
-r <session_id> -n <name> --dangerously-skip-permissions`. The kind stays `claude`: this command
takes the coordinating role, and `commands/spawning.md` keeps that role on Claude Code. The pane
keeps its id and the layout does not move.

`<session_id>` is the basename of the transcript the user chose, without `.jsonl`. `-c` is not a
substitute: it resumes the most recent conversation in the working directory, and two sessions
sharing one directory make that the wrong one. Measured: two sessions both in `~`, where
`-c` could pick either and the restart used `-r <session_id>` instead. For a pane restarted
without a choice, the id of the session it was running is the `session_id` in
`~/.claude/canary/<pane>.json`, with the colon in the pane id written as `-`. A pane that cannot be replaced, because the exit does not complete, gets the resumed
session in a new pane beside it and the user closes the old one.

A previous session that ended through `/exit-agents` left a summary under `~/.claude/handoff`.
One that did not leaves nothing, and the resumed session says so rather than inventing
continuity: the transcript is there and the account of what it was for is not.

## Panes

`herdr` restores the panes of a workspace itself, from `~/.config/herdr/session.json`, which
holds each workspace's `identity_cwd`, the split layout with its ratios, and a `cwd` and `label`
per pane. That restoration does not depend on the previous session having closed cleanly, which
is why it is the source here rather than anything this command writes.

What `herdr` does not restore is the agent inside each pane. Every pane that was working comes
back empty, which is why the helpers question below is asked on a resumed thread as much as on a
new one: it is the step that puts the agents back, one `/spawn-sheep` per selection.

## Questions

Every question goes in one `AskUserQuestion` call, answered in one pass. A session that asks
one thing per turn spends three turns before any work begins.

| Start | Questions |
|---|---|
| new tree, or fresh on a tree with a transcript | what the directory governs, what the session works on, which helpers |
| resumed | the helpers question alone |

A resumed thread carries the first two answers already. It carries nothing about the helpers,
since `herdr` restores panes and not the agents inside them: every pane that was working came
back empty, and the helpers question is what puts them back.

The helpers question is `AskUserQuestion` with `multiSelect: true`, never prose. It brings back a
set in one pass and each selection becomes one `/spawn-sheep` call.

`references/taking-a-tree.md` in `shephrd-protocol` holds what each question offers and where
each option comes from.

## Name

The coordinating session takes the bare name of the directory, which is the address peers hold.
`claude -n <name>` sets it, and `herdr agent rename <pane> <name>` syncs herdr's own record;
both are needed, for the reason `/restart-agents` records.

A live session already holding that name means one of two things. It is still coordinating this
tree, and this pane reports that and takes no role. Or it died without releasing the name, and
retaking it is what running this command in the new pane does.

Taking the role makes this session the one every pane it spawns reports to, and the only one that
reaches the user when those panes run unattended. `/spawn-sheep` writes the name set here into
each pane's `HERDR_REPORTS_TO`, and `shephrd-protocol` is where both halves of that
relationship are written out.

A shephrd has someone above it whenever a god exists, so its `HERDR_REPORTS_TO` carries the god's
name and is not empty. The role is therefore recorded rather than left to that variable:
`python3 ${CLAUDE_PLUGIN_ROOT}/hooks/panes.py --write <pane> <name> <god-name> <scope> --role
shephrd`, with the recipient empty only where no god was declared. Measured: three
panes held `shephrd` with the god above them, and every reader deriving from the recipient
alone called them sheep.

What a role check reads is `panes.py`, which answers `role` from the registry and falls back to
the variable only where nothing was recorded.

## God

When the user declares this session the god, three names change together, and each is a
separate record:

| Record | Command | Value |
|---|---|---|
| herdr workspace | `herdr workspace rename "$HERDR_WORKSPACE_ID" shephrd` | `shephrd` |
| pane label | `herdr pane rename "$HERDR_PANE_ID" god` | `god` |
| Claude session | `claude -n god`, then `herdr agent rename "$HERDR_PANE_ID" god` | `god` |

The role is recorded with `panes.py --write <pane> god "" <scope> --role god --god`. `god` is
the name `/spawn-shephrd` writes into every pane it opens, so a god under
any other name leaves those panes reporting to a session that does not exist.

The session name is the one `SendMessage` addresses, and only a start sets it: a session started
without `-n god` keeps the name Claude built from its directory until it is restarted. Measured:
a god started without `-n` had to be restarted from another pane before peers could reach it.

That restart is delegated. `/restart-agents` forbids a session restarting itself, since the
process running the command is the one that dies, so the god asks a peer in its workspace to run
`/restart-agents` over its pane with the name `god`, and verifies in `ListAgents` after it comes
back. With no peer running, the god reports that the name is not set and the user restarts the
pane.
