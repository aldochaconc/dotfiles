---
name: skill-growth
description: Use when a human corrects a pattern, when the same mistake appears twice, or when a rule is about to be added to a skill, to CLAUDE.md or to adr.md. Sharpen the rule that already covers the case; add one only when none does.
---

# Skill growth

A rule grows from observed failure. A correction sharpens the rule that already covers the
case, and a new rule enters only when none does. A rule with no observed failure behind it
does not belong in a skill, because a skill that accumulates speculative rules stops being
read: the reader cannot tell which rules were paid for.

## What a correction does, in order

Take the first action that applies. Only the last one adds text.

| Action | When | Form |
| --- | --- | --- |
| Sharpen | a rule covers the case and reads imprecisely | edit that line |
| Bound | the rule is right and its admissible case was never named | add the exception to that line |
| Quantify | the rule had no measurable threshold | put the number in the line, and in the gate if one exists |
| Reorder | the rule is right and arrives too late to be read | move it up |
| Delete | the rule was superseded by the correction | remove it |
| Add | no rule covers the case | one line in the section that owns it |

## Gate

A rule entering a skill is never silent. A `SKILL.md` is configuration every future session
reads, and no permission surface covers an edit to it. Before the write, state three things
and stop:

- The exact line, as it will read in the file.
- Which surface takes it, and which of the six actions above applies.
- The observation behind it: what was seen, where, and whether a human corrected it or it
  appeared a second time.

Presenting is not permission. A line shown is not a line approved.

A refused rule is itself an observation: file it in the log of `writing` with the reason,
because the refusal says something about the rule and nothing about the failure that
prompted it.

`~/.claude/hooks/gate-skill-writes.py` runs as `PreToolUse` on `Write`, `Edit`, `MultiEdit`
and `Bash`, and asks on every write to a skill file. An unattended run gets `deny` instead of
a prompt, because a prompt with nobody at the keyboard is a deadlock.

## Where it goes

This table is the routing authority. `CLAUDE.md` points here rather than restating it.

| The mistake was | The rule goes to |
| --- | --- |
| a wrong step, or steps in the wrong order | the skill whose procedure runs those steps |
| a misused flag or a misread command output | the toolbelt row or skill for that tool |
| an action taken without asking | the standard that owns the action, in `~/.claude/CLAUDE.md` |
| a wrong value for this machine: a path, a package, a device, a command | `Rules of this machine` in the repository `CLAUDE.md` |
| a slop pattern in prose, or a form defect in a written artifact | the register in `writing` |
| none of the above, and it has happened twice | `adr.md` |

Appending to the wrong layer is how a tool reference ends up carrying policy: the policy then
drifts, because the source of truth evolved and the copy inside the tool layer did not.

A rule reaches `adr.md` only when no surface above owns it and the failure has appeared twice.
A single occurrence with no owning surface stays in the log of `writing` until it recurs.

## Form

A rule is one line: the imperative, then the failure it prevents.

```
- <imperative>, because <the failure it prevents>.
```

A rule earns more than a line when it carries a shape or a table the imperative cannot
hold. Then it takes a heading, the shape sits under it, and the imperative stays the first
sentence.

The observation stays out of the rule. Every correction files a row in the log of `writing`
with what was seen, where, what triggered it and the uniform correction, and that row is what
makes the rule auditable: a reader deciding whether a rule still applies reads the log, not
the manual. A manual states what to do. The registry of errors is this log.

## When a skill splits

A split is decided by trigger count. A skill splits when it has two triggers that fire in
different situations and share no procedure. It stays whole when one section is an input to
the decision the other makes, and a section whose only trigger is a step of another skill's
procedure is a section of that skill.

## What is not skill growth

Restating what a hook already enforces, a value that lives in a config file, or a fact the
code states. Each is a copy, and a copy is the drift the next correction has to hunt down in
two places.
