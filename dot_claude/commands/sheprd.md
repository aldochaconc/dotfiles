---
description: Take the coordinating role for the tree this session sits in, resuming the previous session there or asking what this one is for
argument-hint: none; the working directory decides everything
allowed-tools: ["Bash", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Shepherd a tree

One session per tree coordinates it: it talks to the user, decides, and asks the other panes for
mechanical work. This command takes that role, and everything it needs comes from the working
directory rather than from arguments.

Run once, right after opening a pane. What follows depends on what the directory turns out to be
and on whether a session worked this tree before.

## Position

The level is read from the tree, not asked. Three cases, each with a different consequence, and
the checks that tell them apart:

| Level | Detected by | What the session governs |
|---|---|---|
| grouping directory | not a git repository, and repositories below it | the projects under it, not any one of their trees |
| repository of repositories | a git repository with repositories nested inside | its own tree plus the nested ones |
| repository | a git repository with none nested | that tree |

Measured on 2026-09-22: one work directory holds five repositories and no repository of its own,
and one repository holds five more nested inside it.

The level is stated at the start, with what it implies. On a tree that is new it is also one of
the questions below, where confirming it costs nothing because the call is being made anyway.
On a tree that is not new it is stated and not asked, since the previous session already worked
under it.

**On a grouping directory**, the work is across projects. A change inside one of them belongs to
a pane opened on that project, which is what `/spawn-agent` is for.

**Reach beyond the tree** is the repository's own business, not this command's. A tree whose
contents are deployed, applied or installed somewhere reaches further than the three levels
above describe, and what that means is written in its `CLAUDE.md`, which every session in it
already reads. This command classifies what git and the filesystem show and states it; a
repository that needs more said reads its own file for it.

## Continuity

A tree that was worked before has a transcript directory under `~/.claude/projects`, named after
the absolute path with every `/` replaced by `-`. Its presence is the test, and it is exact.
Measured on 2026-09-22: 57 transcripts for one repository, 7 for one grouping directory.

| Found | Action |
|---|---|
| a transcript for this directory | relaunch with `claude -c`, which continues the most recent conversation of this directory |
| none | the tree is new to this machine and the session starts from the questions below |

The relaunch replaces the session in place: `herdr agent prompt <pane> "/exit"`, wait for the
pane to leave `herdr agent list`, then `herdr agent start <temp> --kind claude --pane <pane> --
-c -n <name> --dangerously-skip-permissions`. The pane keeps its id and the layout does not
move. A pane that cannot be replaced, because the exit does not complete, gets the resumed
session in a new pane beside it and the user closes the old one.

A previous session that ended through `/exit-agents` left a summary under `~/.claude/handoff`.
One that did not leaves nothing, and the resumed session says so rather than inventing
continuity: the transcript is there and the account of what it was for is not.

## Panes

`herdr` restores the panes of a workspace itself, from `~/.config/herdr/session.json`, which
holds each workspace's `identity_cwd`, the split layout with its ratios, and a `cwd` and `label`
per pane. That restoration does not depend on the previous session having closed cleanly, which
is why it is the source here rather than anything this command writes.

What `herdr` does not restore is the agent inside each pane. A pane that comes back empty is
reported with its label, and starting Claude in it is `/spawn-agent`.

## Questions

Every question this command has goes in one `AskUserQuestion` call, answered in one pass. The
point is starting fast: a session that asks one thing per turn spends four turns before any work
begins, and the answers do not depend on each other.

Asked only when the tree is new:

1. What this session is working on. No file answers it, and every later decision reads against it.
2. Which helpers it needs, by role. Each becomes a `/spawn-agent` call, so asking once opens
   them all instead of one per turn.
3. Whether the derived level is right, offered as options rather than as a yes: Position states
   what it read, and this is where a wrong reading is corrected without costing a turn of its
   own.

The scope of the tree is not asked: the directory is where the tree hangs from, and the table
above says how far it reaches.

A tree that is not new asks nothing. The handoff and the transcript carry what the questions
would have asked, and asking anyway would be asking the user to repeat what is already on disk.

## Name

The coordinating session takes the bare name of the directory, which is the address peers hold.
`claude -n <name>` sets it, and `herdr agent rename <pane> <name>` syncs herdr's own record;
both are needed, for the reason `/restart-agents` records.

A live session already holding that name means one of two things. It is still coordinating this
tree, and this pane reports that and takes no role. Or it died without releasing the name, and
retaking it is the point of `cc --sheprd`.
