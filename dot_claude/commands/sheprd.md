---
description: Take the coordinating role for the tree this session sits in, resuming the previous session there or asking what this one is for
argument-hint: none; the working directory is what the command reads
allowed-tools: ["Bash", "ListAgents", "SendMessage", "AskUserQuestion"]
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
the absolute path with every `/` replaced by `-`. Its presence is the test, and it is exact.
Measured on 2026-09-22: 57 transcripts for one directory, 7 for another.

| Found | Action |
|---|---|
| a transcript for this directory | the user is offered the summary of what it was, and chooses to resume it or to start fresh |
| none | the tree is new to this machine and the session starts from the questions below |

Resuming is offered rather than taken. A transcript proves a session existed here and says
nothing about whether its thread is the one to continue, so what is shown is the summary from
the handoff, or the last exchange of the transcript when there is no handoff, and the choice is
the user's. Starting fresh on a tree that has a transcript is an ordinary answer, not a loss:
the transcript stays where it is.

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
point is starting fast: a session that asks one thing per turn spends three turns before any
work begins.

The questions are ordered but not sequential. Question 1 frames the other two and the user reads
all three before answering any, which is what makes one call enough.

Asked when the tree is new, and when the user chooses to start fresh on a tree that has a
transcript. A resumed session asks none of them: the thread it continues already carries the
answers, and asking would be asking the user to repeat what is on disk.

1. What this directory governs, as options built from what Position read. A directory holding
   repositories is offered as coordinating them, as one project among them, or as neither, and
   the options are written from what was found rather than from a fixed list.
2. What this session is working on. No file answers it, and every later decision reads against it.
3. Which helpers it needs. This is the last question because it reads against both answers
   above, and it is the one with something to show.

Which helpers make sense depends on whether the session coordinates several repositories or
works inside one, which is why question 3 comes after question 1 and reads with it.

### Helpers

`~/.config/herdr/session.json` keeps a `label` and a `cwd` per pane, and both survive the pane
being closed. Measured on 2026-09-22: one workspace held three labelled panes and another held
one labelled and two unlabelled, all with their directory recorded.

The question therefore shows what was there rather than asking into nothing:

| Offered | Built from |
|---|---|
| the panes that were open before, each with its label and directory | the stored panes for this workspace |
| a name per helper, proposed from the repositories found below this directory | the `find` in Position |
| a helper the user names and places | typed in, for work no reading predicted |
| none | starting alone, and `/spawn-agent` opens one later |

A stored pane with no label is offered by its directory, which is what distinguishes it. Its
name is proposed the same way a new helper's is, since a pane that was never named has nothing
to restore.

Each answer becomes one `/spawn-agent` call, which is why the question is a multiple selection
and not a count.

## Name

The coordinating session takes the bare name of the directory, which is the address peers hold.
`claude -n <name>` sets it, and `herdr agent rename <pane> <name>` syncs herdr's own record;
both are needed, for the reason `/restart-agents` records.

A live session already holding that name means one of two things. It is still coordinating this
tree, and this pane reports that and takes no role. Or it died without releasing the name, and
retaking it is the point of `cc --sheprd`.
