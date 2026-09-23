# Roles

Three roles, and what separates them is who may reach the user. The skill carries the table;
this carries why each boundary is where it is.

## The god

A god is declared rather than inferred: a shephrd with no sheep yet looks identical from
outside, and reading that wrong decides whether a question reaches the user at all.

It exists for the case where the user is watching one pane and nothing else, from a phone, while
everything runs unattended. That is also what constrains it: work on a tree goes to a shephrd
rather than to a pane the god opens.

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

## Watchers

What a god does open is watchers, two by default, and they are its own.

A watcher takes no instruction at spawn, only the context and the hierarchy: who the shephrds
are, what tree each holds, and what is already known. It works out what to record from that,
because a god that has to brief its watchers is spending the attention the watchers exist to
save.

It records by default and acts only when told. The backlog, a note in the vault, a mail that has
to go out, a decision written down before it is forgotten: the clerical work around the code,
which no shephrd owns and which the god would otherwise do itself between reports.

Nothing it notices becomes an action of its own. A watcher that sees a stalled pane, a stale
backlog item or a mail that should go out says so and stops there; the god decides whether it
acts. Two watchers taking initiative on what they observe produce two versions of the same note
and two mails, which is the reason this boundary is tighter than a sheep's: a sheep has a scope,
and a watcher has an errand at a time.

| | sheep | watcher |
|---|---|---|
| spawned by | a shephrd | the god |
| arrives with | a task and a scope | the context and the hierarchy |
| writes | code, within its scope | the backlog, notes, mail; never a repository |
| reports to | its shephrd | the god |

The line that matters is the last one in the writes row. A watcher writing code is a sheep
nobody assigned a scope to, which is the overlap `references/not-stalling.md` exists to prevent.
A finding it makes about a tree goes to the god, which routes it to the shephrd that owns it.

Where it writes, measured on 2026-09-23: two Obsidian vaults under `~/Documents`, at `notes` and
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
