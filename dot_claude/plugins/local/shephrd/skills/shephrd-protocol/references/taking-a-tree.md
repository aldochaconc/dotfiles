# Taking a tree

What `/shephrd` asks when a session takes the coordinating role, and what it offers. The
command holds the readings and the order; this holds the questions themselves, because a
session restoring a workspace needs them whether or not anyone typed the command.

## Questions

Every question this command has goes in one `AskUserQuestion` call, answered in one pass. The
point is starting fast: a session that asks one thing per turn spends three turns before any
work begins.

The questions are ordered but not sequential. Question 1 frames the other two and the user reads
all three before answering any, which is what makes one call enough.

Which questions are asked depends on whether the thread is resumed, and the helpers question is
asked either way.

| Start | Questions |
|---|---|
| new tree, or fresh on a tree with a transcript | all three |
| resumed | the helpers question alone |

1. What this directory governs, as options built from what Position read. A directory holding
   repositories is offered as coordinating them, as one project among them, or as neither, and
   the options are written from what was found rather than from a fixed list.
2. What this session is working on. No file answers it, and every later decision reads against it.
3. Which helpers it needs. This is the last question because it reads against both answers
   above, and it is the one with something to show.

Which helpers make sense depends on whether the session coordinates several repositories or
works inside one, which is why question 3 comes after question 1 and reads with it.

A resumed thread already carries the answers to the first two and asking would be asking the user
to repeat what is on disk. It carries nothing about the helpers: `herdr` restores panes and not
the agents inside them, so every pane that was working came back empty. Resuming the coordinator
and leaving its helpers dead is half a restoration, and the helpers question is what completes it.

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

The question goes through `AskUserQuestion` with `multiSelect: true`, never through prose. This is
required rather than preferred. What it brings back is a set: the panes that were working before
are selected together in one pass, and each selection becomes one `/spawn-agent` call. Listing
them in prose and waiting for a typed answer costs a turn per helper and loses the set, which is
the whole point of restoring a workspace rather than opening panes one at a time.

The options are built from the table above, so the user picks from what was there rather than
recalling it. `Other` covers the helper nobody predicted, which `AskUserQuestion` supplies without
an option being written for it.
