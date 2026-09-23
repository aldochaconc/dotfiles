# Keeping a pane moving

A pane stops for two reasons that look identical from outside: a question on screen and a
permission prompt. Both hold the turn, and both hold the report with it. What follows is how
each is avoided.

## What earns a prompt

A master has no hook stopping it, so the judgement is the only gate, and a question put on screen
stops that pane until the user reads it. Measured on 2026-09-22: a coordinating session raised
four options about a defect in a repository it did not own, which another session had already
reported, and its pane sat blocked until the user found it.

The test is two conditions at once. A prompt is earned when the decision is the user's to take,
and when the work cannot proceed under any default.

| Situation | Where it goes |
|---|---|
| a decision that is destructive, irreversible or outside this tree's scope | the user |
| a finding in someone else's tree | one line to the session that owns it, at the end of a turn |
| something already handled by another session | nowhere; it is closed |
| a choice with a defensible default | taken, and reported as taken that way |

A report shaped as a question is the common failure, and it reads as diligence. The tell is that
its options are all about work this session does not own, or that the work continues either way.
Both mean the answer changes nothing and the prompt only costs the user a context switch.

## Commands that stall a pane

A permission prompt stops a turn exactly as a question does, and in a pane nobody is watching it
stops it for as long as nobody looks. The hook denies `AskUserQuestion`; nothing intercepts a
prompt raised by a `Bash` call, so what keeps the pane moving is the shape of the command.

One action per call, which the instructions file already requires and which matters more here. A
permission rule is matched against the whole command line, so chaining setup onto the action puts
the line outside every rule and into a prompt: `cd x && rm -rf y && mkdir y && cd y && git init`
matches nothing and prompts on all of it, with the deletion hidden behind the rest.

| Instead of | Write |
|---|---|
| `cd <dir> && <command>` | `git -C <dir>`, or the absolute path in the command |
| `rm -rf <dir> && mkdir <dir>` | `mkdir -p <dir>` under a fresh name, so nothing needs deleting |
| setup `&&` check `&&` effect | three calls |

What stays prompting is what should. `rm -rf` and `sudo` are listed under `ask` because the user
reserves those, and a slave inherits that rather than escaping it: a pane running unwatched is a
reason to write commands that do not need the prompt, never a reason to route around one. A
command that genuinely needs the decision goes to the master with the rest.

At least one message per turn, carrying three things. A turn that also sent a blocking question
sends the report as well: the question asks for a decision, the report says where the work stands,
and neither substitutes for the other.

| Part | Content |
|---|---|
| done | what the turn produced, by file or by outcome |
| in flight | what is running or half-finished, so the master knows what a next turn continues |
| blocked | what is waiting on a decision, naming who has to make it |

A turn that produced nothing still reports that it ran. Silence and a dead session read the same
from outside, and the master acts on the difference.

A master reports to nobody and keeps the same accounting for itself, because `/exit-agents` and
`/agents-budget` read it.

### Focus

A session working directly with the user reports the same three parts, plus any decision the user
made that changes the plan.

The dialogue does not travel. The master needs the state and the decision; a transcript fills its
context with what already exists in the other pane.

That decision is what keeps the other slaves correct. A choice the user makes in one pane can
contradict the assumption another pane is working under, and the master is the only session
positioned to see both.

## Work found is work routed

A finding is not an assignment to whoever found it. A master that repairs what it notices fills
its own context with work any pane could have done, and the context it spends is the one holding
the map of every other pane.

Two questions decide where a finding goes, in this order.

| Question | Answer | Where it goes |
|---|---|---|
| Was a pane already working on this? | yes | back to that pane, as one message |
| Does the repair take more than a turn? | yes | a new pane opened for it, with `/spawn-agent` |
| Neither | | the master does it |

The first question outranks the second. A pane that was building the thing holds why it is the
way it is, and a second pane repairing it in parallel produces two versions of one file. Handing
it back costs one message; discovering the conflict costs both attempts.

Measured on 2026-09-23: a master found that one pull request body did not follow the
repository's template, offered the user three options, and put itself first. The session that
wrote the other three bodies correctly had just restarted with fresh context and was not
offered at all.

What makes this hard to see is that the finding arrives already understood. The master has read
the file and knows the repair, so doing it feels shorter than explaining it. The cost that is not
felt is the context, which is spent for the rest of the session.

A finding routed to a pane goes with what the pane needs to act: what is wrong, where, what was
measured, and what the repair is if it is known. A message saying only that something is wrong
makes that pane re-derive what the master already has.
