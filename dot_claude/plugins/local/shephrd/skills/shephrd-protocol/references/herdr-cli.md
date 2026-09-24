# herdr CLI

Every row was measured in this machine's workspaces. What each one records is a
failure that a plausible command produces.

## Three name records

herdr keeps an agent name per pane and a label per pane, and Claude Code registers its own
session name. Three records, written by three commands, disagreeing by default.

| Command | Which record it writes | Read by |
|---|---|---|
| `claude -n <name>` | the Claude side, and the terminal title with it | `ListAgents`, `SendMessage` |
| `herdr agent rename <pane> <name>` | herdr's agent record | `herdr agent list` |
| `herdr pane rename <pane> <name>` | the pane label | the sidebar, `session.json`, `/shephrd` |

Only the first is an address. The other two are what a person reads, and a pane missing its
label shows as a number: Measured: two panes carried none and one carried
`skills-agent` while its session answered to `skills-swe`.

`herdr tab rename <tab> <name>` is a fourth, one per workspace rather than per pane. A tab whose
`label` equals its own number was never named, which is how all three tabs read on that date.

Running the rename by itself after a restart leaves the pane reading correct in
`herdr agent list` while peers still address a generated name.

Without `-n`, Claude builds a name from the basename of the working directory plus a suffix: two
panes in one repository restarted without it came back as `<basename>-9e` and `<basename>-a2`. The
generated name never agrees with herdr's record because it never reads it.

Verify a name in `ListAgents`, never in `herdr agent list`.

## Starting an agent

```
herdr agent start <name> --kind <kind> --pane <pane> -- <start>
```

Everything after `--` goes to the agent's binary. For `claude`, `<start>` is `-n <name>
--dangerously-skip-permissions`; the Agents table in `commands/spawning.md` holds it per kind.

The permission mode is set at launch and is not stored in settings. A pane started without the
flag comes up asking, and what it asks about includes messages from other sessions: a pane in the
default mode holds them for the user to approve and they expire unanswered. Measured after four
panes were restarted without it: three peer messages lost, one refused and two expired.

The flag does not cover a project hook, which is the limit worth knowing before relying on it.
Hooks run in every mode and decide on their own, so a hook returning `permissionDecision: "ask"`
raises a prompt the flag was supposed to remove. Measured: a pane launched with the
flag stopped on every `git` write, because the repository's own `PreToolUse` hook answered `ask`
each time. The pane reports `idle`, since the interface is waiting on a human, and a queued
message or a new prompt sits behind the open dialog rather than replacing it.

A pane running unwatched in a tree with such a hook therefore stops at the first intercepted
command, whatever was passed at launch. What unblocks it is answering on screen, or the hook's
own unattended switch where it has one. That switch belongs to the repository and is the
repository's to set: a hook is a security surface and this plugin neither edits nor routes around
one.

`agent_name_taken` comes back while herdr still holds a record under that name, including one
whose agent has exited. A restart therefore starts under a temporary name and renames afterwards.
A pane id is not a legal name: a name starts with a lowercase letter and carries lowercase
letters, digits, `-` or `_`.

## Exiting

`herdr agent prompt <pane> "/exit"` closes an interactive session. Measured on 2026-09-24: the
pane left `herdr agent list` four times, on a work shephrd at 14:56, on `os` and
`protocol-refine` around 15:30, and on the same work shephrd again at 15:41.

A session of kind `bg`, one that has passed under Claude Code's background sessions service, is
not closed by it. The one failure that day, at 16:07 on `w1Z:p1`, was on a session `ListAgents`
already listed as `bg`: the prompt moved it to the background sessions panel ("describe a task
for a new session", over a list of sessions) and the pane never left `herdr agent list`. Two
`C-c` sent with `herdr agent send-keys` brought the session back into the pane. The installed
binary was Claude Code 2.1.281.

So a `/exit` is preceded by reading the pane's kind in `ListAgents`. An interactive session takes
the `/exit`; a `bg` one is reported and left as it is.

The background service also renames the session after its task. `ListAgents` showed
`verify-owner-field-migration` of kind `bg` for a session started with `-n <shephrd>`, and the
`session_id` changed from `8d8e76d6` to `c2cf006a`. `herdr agent prompt <pane> "/rename <name>"`
repairs the name: `ListAgents` showed it within 1 s, with no restart and the thread kept.

not verified: why the start at 15:41 ended as `bg`, and what ends a `bg` session. Neither is to
be tested on a pane holding work. `herdr pane close <pane>` removes the pane and the process with
it, which is a close rather than an exit and leaves no shell to relaunch in.

`herdr agent send-keys <pane> ctrl+d` does not end a session either. The call returns `ok` and
the agent stays alive.

## Reaching a blocked pane

A pane showing a dialog refuses every prompt: `agent_blocked: agent <pane> is blocked and
requires interactive input`. The three channels differ in what the block stops.

| Channel | Reaches a blocked pane | What it is for |
|---|---|---|
| `herdr agent prompt` | no | a turn the session answers |
| `herdr agent send-keys` | yes | keystrokes the terminal takes, above the agent |
| `SendMessage` | queued behind the dialog | anything the session reads when it next runs |

`herdr agent send-keys <pane> Escape` dismisses the dialog. Measured: a pane
blocked over an hour returned `{"type":"ok"}`, moved from `blocked` to `done`, and kept its
context at 9%. Nothing else recovers such a pane without the user touching the keyboard.

What Escape costs is the dialog's content. A question with four analysed options loses the
analysis, not just the prompt, so the pane is read first and the user decides.

The exit is not immediate. In the interval `herdr agent read` returns the shell prompt with
Claude's status bar still drawn, so a pane that has already exited reads as alive. The signal is
the pane disappearing from `herdr agent list`; `agent start` before that fails with
`agent_pane_busy: is not an available shell`.

## Waiting

`herdr agent wait <pane> --until idle --until done --timeout <ms>` blocks until the session settles; a pane whose last turn finished reports `done`.

A message sent to a session reported as `working` is queued and delivered when its turn ends, so
asking costs nothing but the wait and the turn is never interrupted. An exit sent mid-turn
discards whatever the turn was producing.

Whether the wait carries a timeout depends on what expiry would mean. A restart uses one, because
a session that never settles holds the whole restart open. A close does not, because a timeout
would decide by expiry the same question the user was just asked.

## Layout

`herdr pane layout --pane "$HERDR_PANE_ID"` returns the calling session's workspace.

Without `--pane` it returns the layout of whichever workspace the user is *looking at*. Measured:
a session in one workspace read back the three panes of another. A spawn computed from that
layout opens in the wrong workspace or fails.

`herdr pane split <target>` carries the same defect when `<target>` is omitted: the split falls
back to the focused pane, which can sit in another workspace.

`herdr pane run` is for a pane holding a shell and nothing else. Against a pane running an agent
there is no shell to receive it: the text enters that session's message queue as if the user had
typed it, and waits there for its next turn. It returns no output and no error, so it reads like
a slow command, and retrying queues a second message. Measured: two probes for an
environment variable landed in one pane that way.

What a pane with an agent is asked, it is asked with `herdr agent prompt`, which enters as a turn
and is answered. What is read about it without disturbing it comes from
`~/.claude/panes/<pane>.json` and `~/.claude/canary/<pane>.json`.

Reading a shell pane immediately after `herdr pane run` can return the prompt before the output. Repeat
the read rather than believing the first one.

## Persistence

`~/.config/herdr/session.json` holds each workspace's `identity_cwd`, the split layout with its
ratios, and a `cwd` and `label` per pane. Both survive the pane being closed: measured, one
workspace held three labelled panes and another held one labelled and two unlabelled, all with
their directory recorded.

herdr restores the panes of a workspace from that file, and it does not restore the agent inside
them.
