# Roles

Four roles, and what separates them is who may reach the user. The skill carries the table;
this carries why each boundary is where it is.

## The god

A god is declared rather than inferred: a shephrd with no sheep yet looks identical from
outside, and reading that wrong decides whether a question reaches the user at all.

It exists for the case where the user is watching one pane and nothing else, from a phone, while
everything runs unattended. That is also what constrains it: work on a tree goes to a shephrd,
which the god opens with `/spawn-shephrd`, rather than to a sheep of its own.

It is named `god`, its pane is labelled `god`, and its herdr workspace is named `shephrd`;
`/shephrd` sets the three when the user declares it. `god` is the name `/spawn-shephrd` and
`/spawn-watcher` write into every pane they open. Only a start with `-n god` sets the session
name, and `/restart-agents` forbids a session restarting itself, so a session declared god after
starting under another name is restarted by a peer. Measured: a god started without `-n` had to
be restarted from another pane before peers could reach it.

Its own location does not matter, and this is the difference that shapes the whole registry. A
shephrd is defined by where it stands: the tree under it is what it holds, what its scope is
written against, and what `/shephrd` reads to take the role. A god holds no tree, so it can sit
in any directory on the machine.

That is why the registry is keyed by `pane_id` under `~/.claude/panes` rather than by working
directory. A god opened anywhere resolves its own role from the same file every other pane uses,
and moving it breaks nothing. A shephrd that moves is a different shephrd, which is the correct
reading rather than a defect.

What a god reads instead of a tree is the registry itself: every pane, who it reports to, and
what it holds. `hooks/panes.py` answers that for one pane, and the canary's beats answer which
are still alive.

One command belongs to the god alone. `/flood` closes every shephrd and every sheep, leaving the
god and its watchers, so the next start is from nothing. A shephrd running it would be closing
its peers and then itself; a sheep cannot close anything. It touches no working tree: sessions
end, and what they wrote stays written.

## Answering a dialog from the god

A dialog open in any pane is reachable from the god. `herdr agent send-keys <pane> <key>` takes
`Enter` for the highlighted option, a digit for one by number, arrows to move and `esc` to
dismiss: Measured: an `Enter` approved a skill edit in a sheep's pane and moved it
from `blocked` to `working` in seconds.

That is what keeps the user in one window. Walking to each pane is what the god exists to
replace, so the god reads the dialog, brings what is the user's here, and sends the key they
choose.

What the god answers on its own, and what it brings:

| Dialog | Where it is answered |
|---|---|
| a sheep asking about its own work | redirected to its shephrd, which owns that decision |
| a question already answered elsewhere | dismissed with `esc`, saying so |
| a permission prompt, a skill edit, a destructive command, a commit | the user, through the god |

The line is what the user's own configuration reserves. A gate that asks exists so a human sees
what passes it, and a god answering on their behalf defeats the gate rather than serving it: the
god is the window, not a substitute for the person at it.

Read the pane before sending any key. `esc` discards whatever a dialog was asking, and an
`Enter` lands on whichever option is highlighted rather than on the one that was meant.

One `Enter` does not close a series. A call carrying several questions advances to the next one,
and the last lands on a confirmation screen that wants its own `Enter`; the pane reads `blocked`
throughout. Measured: three were needed, and checking `herdr agent list` after the
first made the key look like it had failed. Read the pane again between keys rather than counting
them.

## Watchers

Beside shephrds, a god opens watchers, two by default, with `/spawn-watcher`.

A watcher takes no instruction at spawn, only the context and the hierarchy: who the shephrds
are, what tree each holds, and what is already known. An errand builds on that context, so the
god does not brief a watcher from nothing each time it sends one.

A watcher with no errand is at rest. It does not investigate, measure or record on its own
initiative, and a turn at rest runs no tool and sends no message: `report-gate.py` lets a
watcher end such a turn without a report. Measured: before that exemption the gate forced a
watcher at rest to reply to the god after the god had told it not to.

An errand is what moves it. The backlog, a note in the vault, a mail that has to go out, a
decision written down before it is forgotten: the clerical work around the code, which no
shephrd owns and which the god would otherwise do itself between reports. The watcher reports
when the errand is done and returns to rest.

Nothing it notices becomes an action of its own. A watcher that sees a stalled pane, a stale
backlog item or a mail that should go out says so and stops there; the god decides whether it
acts. Two watchers taking initiative on what they observe produce two versions of the same note
and two mails, which is the reason this boundary is tighter than a sheep's: a sheep has a scope,
and a watcher has an errand at a time.

| | sheep | watcher |
|---|---|---|
| spawned by | a shephrd | the god |
| arrives with | a task and a scope | the context and the hierarchy, then one errand at a time |
| writes | code, within its scope | the backlog, notes, mail; a repository only when an errand assigns it |
| reports to | its shephrd | the god |

The line that matters is the writes row. Writing to a repository is not a watcher's job by
default: a watcher writing code on its own is a sheep nobody assigned a scope to, which is the
overlap `references/not-stalling.md` exists to prevent. An errand that assigns a repository is
the scope, naming the paths and what stays out as a spawn does for a sheep, and the write ends
with the errand.
A finding it makes about a tree goes to the god, which routes it to the shephrd that owns it.

Where it writes: two Obsidian vaults under `~/Documents`, at `notes` and
at `Obsidian Vault`, with `obsidian-markdown` and `obsidian-bases` holding their syntax. Mail
arrives through the account's MCP rather than through settings, so a session without it reports
that rather than failing.

Two is the default because one watcher is a single point of attention and a third has nothing
distinct left to notice. The number is not a rule: a god running one tree needs fewer, and the
user says so.

What makes the window usable is what does not arrive. Every shephrd gates before sending, and
four things pass:

- a decision only the user can take: destructive, irreversible, or outside that tree's scope
- a tree that is blocked, meaning the shephrd itself cannot proceed, not one of its sheep
- a milestone that landed, in one line
- a command needing elevation, since `pkexec` raises a prompt on a screen only the user has

Everything else is the shephrd's to resolve, including its own sheep's questions. A shephrd
that forwards each one turns the single window into the noise it was built to replace.

## Shephrds among themselves

Shephrds talk to each other directly. One tree depends on another, a branch lands that a second
tree was waiting on, a defect belongs to a repository someone else holds: that traffic goes
peer to peer, and routing it through the god would make the one window a relay.

What they do not settle between themselves is a decision. Two shephrds disagreeing on who owns
a path, on what order two trees land in, or on whether something may be discarded, take it to
the god rather than agreeing on it: a peer cannot grant what only the user can, and two
sessions converging on an answer nobody authorised is how permission gets laundered.

The test is what the exchange produces. Information moves sideways; a decision moves up.

## The heartbeat

A shephrd sends the god a heartbeat every five of its own turns, or sooner when a session it
holds has gone quiet for long enough to be worth naming. Every session it holds is inside it.
This is separate from the per-turn report a sheep sends its shephrd: the sheep reports work, and
the shephrd reports movement.

The timeout is what makes silence legible. Five turns of a busy shephrd pass in minutes, and
five turns of one that is itself waiting may never arrive: a shephrd blocked on a dialog takes
no turns at all, so a count alone reports nothing exactly when something is wrong. A sheep whose
canary beat has not moved in fifteen minutes while the shephrd took turns is the case worth
sending early, and the beat under `~/.claude/canary` is where that is read rather than guessed.

What it carries is what moved, in one line each:

| Part | Content |
|---|---|
| moved | what advanced since the last heartbeat, by outcome rather than by step |
| in flight | what each sheep is on now |
| waiting | what is blocked, and on whom |

Silence is a state and is reported as one. Five turns that advanced nothing says exactly that,
and it is more useful than no message: it distinguishes a tree that is stuck from one the god
simply has not heard from.

Five turns rather than a clock, because a shephrd's turns are the unit of its own work. A busy
shephrd reports often and an idle one rarely, which is the cadence the god wants without anyone
measuring elapsed time.

What it is not is a liveness check. The canary at `~/.claude/canary` already answers who is
taking turns, and `canary-read.py` prints it oldest first. A heartbeat that only said a session
was alive would duplicate a file that is already written on every turn by every pane. It exists
for what the canary cannot see: whether the work is moving.

A god does not send one. It is the window rather than a session anything watches, and a watcher
reports when its errand is done rather than on a count.
