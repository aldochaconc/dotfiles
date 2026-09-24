# shephrd

Coordinate Claude Code sessions running in terminal panes. A sheep reports to the session that
opened it, which is a shephrd or the god. A shephrd reports to the god, and only the god reaches
the user.

## Requirements

`herdr`, the terminal workspace manager that owns the panes. `herdr --version` answers whether it
is installed. Nothing in this plugin works without it.

## Install

The plugin is served by a local marketplace written from the dotfiles source:

```
claude plugin marketplace add ~/.claude/plugins/local
claude plugin install shephrd@machine-local
```

`bootstrap.sh` replays both from `claude-marketplaces.txt` and `claude-plugins.txt`.

Editing the plugin means editing the chezmoi source and running `chezmoi apply ~/.claude/plugins`.
A `directory` marketplace loads the plugin in place, so an edit takes effect at the next session
start or `/reload-plugins`; bump `version` in `plugin.json` when the recorded version should move
with it.

## Components

| Component | What it is for |
|---|---|
| `shephrd-protocol` skill | who may talk to the user, who reports to whom, what unattended means per role |
| `ask-gate.py` hook | denies `AskUserQuestion` where the registry records a session above the pane, except during a turn the user typed |
| `typed-mark.py` hook | records on `UserPromptSubmit` whether the prompt came from the keyboard or from a peer |
| `confirm-gate.py` hook | runs a command marked `# shephrd:confirm` only against a root-owned approval record for that pane and command |
| `report-gate.py` hook | holds a turn that a sheep would end without reporting, and a shephrd's while its god is attended |
| `canary.py` hook | writes a liveness beat at the end of every turn, so a stalled pane is visible |
| `canary-read.py` | prints the beats oldest first |
| `panes.py` | who a pane answers to, kept outside the process a restart replaces |
| `hierarchy-auditor` agent | which panes exist, which names reach them, which are stalled |
| `traffic-auditor` agent | who reported, who went silent, which question is waiting |
| `/project-manager` | open the pane that tracks state, plans, and holds the boundaries |
| `/shephrd` | take the coordinating role for the tree this session sits in, or name the god |
| `/spawn-sheep` | open a sheep under this session, carrying its name, root and who it reports to |
| `/spawn-shephrd` | open a shephrd on a tree, reporting to the god |
| `/unattended` | tell a god or shephrd the user has stepped away; a sheep is already unattended |
| `/restart-agents` | restart panes so they pick up new permissions and hooks, keeping their names |
| `/exit-agents` | close panes after each session writes what it was doing |
| `/flood` | close every shephrd and its sheep, leaving the god: the god's command |
| `/agents-budget` | report context and account limits per session |
| `/resolve` | collect every herd's state and stoppers, put the stoppers to the user in batches, send each answer back |

The commands are typed by a person. The skill loads on its own, which is the point: a spawned pane
never types a slash command and still has to know it answers to someone.

## Tests

Every hook answers `--selftest`, and the exit code is the result: a failing check raises and the
run exits non-zero. `for h in hooks/*.py; do python3 "$h" --selftest; done` runs them all.

A run prints that it passed and no count. A hardcoded total cannot see a check that was deleted,
which is the direction a suite decays in: Measured: four assertions removed from a
copy of `canary-read.py` left it printing `21 checks passed` and exiting 0, with seventeen
assertions in the file. What changed between two revisions is what `git diff --stat` answers, and
it answers it including the deletions.

A count derived from what the checks are is a different case and stays.
`~/.claude/hooks/gate-attended.py` sums the lists it tests, so a case removed from a list removes
itself from the total. The rule is against a number written by hand, not against counting.

## Hierarchy

`HERDR_REPORTS_TO` names the session a pane answers to, and the two spawn commands set it through `commands/spawning.md`. It answers
nothing else: an empty value means the spawn did not set it or a restart cleared it, never that
the session coordinates itself.

What a pane is comes from its record in `~/.claude/panes/<pane>.json`, which carries the role
beside the name, the recipient and the scope. `python3 hooks/panes.py` resolves it, reading the
variables first and the record for what they lost. `herdr agent list` carries none of this, and
the variable does not survive a restart, which is why the record exists.

Unattended is the default state of a pane and being watched is what a session opts into, so
`/unattended` is a command for a god or a shephrd. The variable is not that switch: it says who a
pane reports to and answers nothing about whether the pane may ask. `shephrd-protocol` holds the
mode per role and what releases a pane from it.

## Other agents in panes

`/spawn-sheep --kind <kind>` opens a sheep running another agent that `herdr agent start`
accepts. A shephrd and a god stay on Claude Code, since they answer through `SendMessage` and
`ListAgents`. The Agents table in `commands/spawning.md` holds the arguments per kind, which of
them were verified, and what a missing one does to the procedure. Two kinds are verified there,
`claude` and `codex`; every other kind is refused rather than started with guessed flags.

A pane running anything but `claude` runs without the three hooks. Its kind is the `agent` field
of `herdr agent list`, and the protocol treats such a pane as ungated: no beat is written, its
report is not assumed, and silence from it is not read as a report.

## Known limits

The end-of-turn reporting rule cannot be delivered by this skill. A skill description is matched
against an incoming prompt and the end of a turn has none, so the rule is carried by the
`# Machine` paragraph of `~/.claude/CLAUDE.md`, which is reinjected every turn. Trimming that
paragraph disables the rule silently.

A new machine adds it to `~/.claude/CLAUDE.md` by hand, as it reads here:

```
A session running in a pane answers to whoever spawned it. `HERDR_REPORTS_TO` carries that name,
and `python3 ~/.claude/plugins/local/shephrd/hooks/panes.py` answers it along with the role, from
the registry when a restart emptied the variable.

A name there means this session reports to it: a sheep of a shephrd at the end of every turn, a
shephrd under a god at the end of every turn only while the god is attended, and otherwise only
for a decision beyond its tree or finished work. A sheep the god opened reports to the god only
what other sessions have to learn: a skill or rule changed, a session closed or restarted, a
permission or hook changed, anything that widens or cuts what the other agents can do alone. Work
that stays inside its own scope is not reported. The same holds for a shephrd whose tree no other
session depends on: `os` changing the bar touches no other session's code or work. A decision with a defensible default is taken and reported as
taken; only an action the Git section reserves to the user, a write outside the scope, or a
choice no default covers goes to it, never to the user. Empty means the session coordinates its
own tree, and a god reaches the user directly: that one is declared with `HERDR_GOD` or in the registry,
never inferred.

Load `shephrd-protocol` before messaging a peer, before asking the user anything from a pane, and
whenever the mode is unattended.
```

The `panes.py` path is the one this marketplace installs to; a plugin installed from another
marketplace takes its own install path there.

The prohibition on a sheep calling `AskUserQuestion` is enforced by `hooks/ask-gate.py`, a
`PreToolUse` hook that denies the call where the registry records a session above the pane. The
denial names the route rather than closing the question: the decision goes to the shephrd by
`SendMessage`, carrying what is blocked and what each option costs, and the shephrd escalates to
the god only for what is beyond its tree. A master absent from `ListAgents` is the one case a
sheep addresses the user directly.

Reading `HERDR_REPORTS_TO` instead of the record was wrong in both directions, measured on
a shephrd reporting to the god carries the variable and was denied, and a restarted
pane loses it and was not. A pane with nothing recorded above it proceeds. A sheep is released
only during a turn the user typed, which `hooks/typed-mark.py` marks; `attended: true` in its
record does not release it.

`confirm-gate.py` depends on a root helper and a polkit policy that the plugin cannot install:
`/usr/local/lib/shephrd/approve` and `local.shephrd.approve`, whose source lives beside the
dotfiles that ship this plugin. On a machine without them, every command marked
`# shephrd:confirm` is denied, and the denial names the missing approval.

Hooks are read once at launch, so a pane started before the plugin was installed does not have
it.

Nothing enforces the rule against commands that wait on input. A denial covers one tool; an
interactive prompt inside a `Bash` call is not a tool call the hook can see.

`--dangerously-skip-permissions` does not cover a project's own hooks. A repository hook that
returns `permissionDecision: "ask"` raises a prompt in the pane whatever was passed at launch, and
an unwatched pane stops there reporting `idle`. Measured: in a tree whose hook
intercepts every `git` write. The canary is what makes that visible; unblocking it belongs to the
repository that owns the hook.

`~/.claude/handoff` is created by the first `/exit-agents` run that writes into it. Until then
`/shephrd` finds no handoff and says so.
