---
description: Clear the queue of stoppers across every herd in one pass, so the herds can keep working without waiting on the user
argument-hint: none; run by the god over every herd, or by a shephrd over its own tree
allowed-tools: ["Bash", "Read", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Resolve

A herd stops when a decision it cannot default reaches the user one at a time, from whichever
pane raised it. This command collects every open decision in one turn, puts them to the user in
batches, and sends each answer back to the pane that asked. It ends when the queue is empty.

The god runs it over every shephrd and every sheep reporting to it directly. A shephrd runs it
over its own sheep only, and passes up to the god what is beyond its tree. Load
`shephrd-protocol` first: it holds who reports to whom and what a sheep may decide alone.

## 1. Ask for state

`ListAgents`, then one `SendMessage` to every recipient in the same turn, asking for its state in
this fixed form:

```
Done: <one line>
In progress:
- <one line per item>
Pending:
- <one line per item>
Stoppers:
- <question>
  a. <option>: <consequence>
  b. <option>: <consequence>
```

Each stopper carries its question, two to four options and the consequence of each one. A
stopper can also be a question to settle before planning, of the kind `grill-me` asks: it goes
in the same list, since it blocks the same way.

Wait with `SendMessage` and `notify_when_idle: true` on each recipient, never with a foreground
wait. A turn held on a wait holds this session's own report, and the notices arrive on their own.

A recipient counts as not answering when its `[Cross-session idle notice]` arrives with no reply,
or says the subscription expired. Its row is then read from what it left on disk, in order: its
snapshot, `~/.claude/handoff/<name>-snapshot.md`; its handoff of the day,
`~/.claude/handoff/<name>-<date>.md`; and its canary beat, `~/.claude/canary/<pane>.json` with
the colon of the pane id written as `-`, for when it last took a turn. A pane that is alive and
busy has usually written neither file today, so its row says which source was used and how old
it is, or `no reply, no record` when there is none. The table goes out once every recipient has
answered or been read this way, including when nobody answered.

## 2. Show the table

One row per herd, with the god's direct sheep as rows of their own:

| Herd | Done | In progress | Pending | Stoppers |
|---|---|---|---|---|

A row read from disk rather than from a reply names its source and age, for example
`(snapshot, 2h)`. A herd with nothing blocked reads `none` in its Stoppers cell.

## 3. Resolve the stoppers

Every stopper goes to the user through `AskUserQuestion`, up to four questions per call, and the
calls repeat until the queue is empty. In a shephrd's run, a stopper beyond its tree goes to the
god by `SendMessage` instead, with its options and consequences, and the rest go to the user as
here. Prose options in the reply are not a question: they scroll
away and the answer goes with them.

- Each question keeps the options and consequences its owner wrote, and names the herd.
- `multiSelect` goes on a question whose options do not exclude each other.
- A stopper the environment can answer is looked up rather than asked. The answer goes back
  naming the command that produced it, and is never presented as the user's.
- Related stoppers from different herds go in the same call, so the user sees them together.

## 4. Send the answers down

Each answer goes by `SendMessage` to the owner of the stopper, quoting the question and the
option chosen. The owner acts on it and records it in the Decisions section of its snapshot,
`~/.claude/handoff/<name>-snapshot.md`, or in its handoff of the day when it has no snapshot, so
the answer survives the pane. This holds for a shephrd and for a sheep reporting to the god
directly.

An answer is an instruction from the session above. It is not an approval of a reserved action:
a force-push, a merge, a write to trunk or a destructive command still goes through the polkit
record under "An irreversible action" in `shephrd-protocol`.

## 5. Report

With the queue empty, one line per herd saying what is still running.
