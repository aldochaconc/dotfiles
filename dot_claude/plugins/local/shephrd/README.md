# shephrd

Coordinate Claude Code sessions running in terminal panes. One session per tree talks to the user
and decides; the others do mechanical work and report to it.

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
| `ask-gate.py` hook | denies `AskUserQuestion` in a spawned pane, where nobody is watching to answer |
| `report-gate.py` hook | holds a turn that a slave would end without reporting |
| `canary.py` hook | writes a liveness beat at the end of every turn, so a stalled pane is visible |
| `canary-read.py` | prints the beats oldest first |
| `roster.py` | who a pane answers to, kept outside the process a restart replaces |
| `hierarchy-auditor` agent | which panes exist, which names reach them, which are stalled |
| `traffic-auditor` agent | who reported, who went silent, which question is waiting |
| `/shephrd` | take the coordinating role for the tree this session sits in |
| `/spawn-agent` | open a pane, carrying name, root and master into it |
| `/unattended` | tell a master the user has stepped away; a slave is already unattended |
| `/restart-agents` | restart panes so they pick up new permissions and hooks, keeping their names |
| `/exit-agents` | close panes after each session writes what it was doing |
| `/agents-budget` | report context and account limits per session |

The commands are typed by a person. The skill loads on its own, which is the point: a spawned pane
never types a slash command and still has to know it answers to someone.

## Hierarchy

`HERDR_AGENT_MASTER` names the session a pane answers to. `/spawn-agent` sets it. A value there
means this session reports to that name and asks it rather than the user for any decision; an
empty value means the session coordinates itself.

That variable is also the unattended switch. A slave is unattended from its first turn because
nobody is watching the pane it opened in, so `/unattended` is a command for a master.

Nothing in `herdr agent list` records this, which is why the variable exists.

## Known limits

The end-of-turn reporting rule cannot be delivered by this skill. A skill description is matched
against an incoming prompt and the end of a turn has none, so the rule is carried by the
`# Machine` paragraph of `~/.claude/CLAUDE.md`, which is reinjected every turn. Trimming that
paragraph disables the rule silently.

The prohibition on a slave calling `AskUserQuestion` is enforced by `hooks/ask-gate.py`, a
`PreToolUse` hook that denies the call when `HERDR_AGENT_MASTER` is set. Hooks are read once at
launch, so a pane started before the plugin was installed does not have it.

Nothing enforces the rule against commands that wait on input. A denial covers one tool; an
interactive prompt inside a `Bash` call is not a tool call the hook can see.

`--dangerously-skip-permissions` does not cover a project's own hooks. A repository hook that
returns `permissionDecision: "ask"` raises a prompt in the pane whatever was passed at launch, and
an unwatched pane stops there reporting `idle`. Measured on 2026-09-22 in a tree whose hook
intercepts every `git` write. The canary is what makes that visible; unblocking it belongs to the
repository that owns the hook.

`~/.claude/handoff` is created by the first `/exit-agents` run that writes into it. Until then
`/shephrd` finds no handoff and says so.
