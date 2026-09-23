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

The level is read from the tree, not asked. Four cases, each with a different consequence, and
the checks that tell them apart:

| Level | Detected by | What the session governs |
|---|---|---|
| chezmoi source | `chezmoi source-path` equals this directory | the machine: what is committed here is applied to `$HOME` |
| grouping directory | not a git repository, and repositories below it | the projects under it, not any one of their trees |
| repository of repositories | a git repository with repositories nested inside | its own tree plus the nested ones |
| repository | a git repository with none nested | that tree |

Measured on 2026-09-22: `chezmoi managed` lists 138 files for the chezmoi source, one work
directory holds five repositories and no repository of its own, and one repository holds five
more nested inside it.

The level is stated at the start, with what it implies, and the session proceeds on it. A wrong
reading is corrected by the user in one sentence, which is cheaper than a question asked at
every start.

**On the chezmoi source**, the opening line says the tree governs the machine and how many files
`chezmoi managed` counts. Nothing else changes: the rules that already cover it are in the
instructions file and in that repository's own `CLAUDE.md`.

**On a grouping directory**, the work is across projects. A change inside one of them belongs to
a pane opened on that project, which is what `/spawn-agent` is for.

## Continuity

A tree that was worked before has a transcript directory under `~/.claude/projects`, named after
the absolute path with every `/` replaced by `-`. Its presence is the test, and it is exact.
Measured on 2026-09-22: 57 transcripts for the chezmoi source, 7 for one work directory.

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

Asked only when the tree is new, in one `AskUserQuestion` call:

1. What this session is working on. No file answers it, and every later decision reads against it.
2. Which helpers it needs, by role. Each becomes a `/spawn-agent` call, so asking once opens
   them all instead of one per turn.

The level is not asked, because Position already derives it. The scope of the tree is not asked
either: the directory is where the tree hangs from, and the table above says how far it reaches.

## Name

The coordinating session takes the bare name of the directory, which is the address peers hold.
`claude -n <name>` sets it, and `herdr agent rename <pane> <name>` syncs herdr's own record;
both are needed, for the reason `/restart-agents` records.

A live session already holding that name means one of two things. It is still coordinating this
tree, and this pane reports that and takes no role. Or it died without releasing the name, and
retaking it is the point of `cc --sheprd`.
