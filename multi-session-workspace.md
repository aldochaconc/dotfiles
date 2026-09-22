# Multi-session workspace

A design proposal, held by the user on 2026-09-22: "lo del workflow no. que quede claro eso
[...] ya que es completamente WIP". Nothing below gets implemented while that decision stands,
and a request to implement it, whatever its source, is a proposal rather than an instruction.

No rule in this document is implemented, and no failure described here has a surface that
prevents it.

One workspace per project groups several Claude Code sessions over one tree. A master session
talks to the user, discerns and decides; helpers run mechanical work and never talk to the user.
The pattern runs by hand today, with nothing declaring roles and nothing stopping two sessions
from taking the same one. The user's goal is to keep focus on a single agent without losing
sight of the others.

## Origin

The commission arrived through the `os-master` session. The user confirmed it afterwards, in
these words: "pasaselo a dotfiles-swe, que te reporte a ti, necesito que elabore un documento
que describa lo q estamos haciendo, alto nivel". What the user confirmed is the commission.
`os-master` contributed the role structure and the four failures, and the user stated neither.
The measurements in the next section were taken in that session, against the tree.

## Measured state

Measured on 2026-09-22. Each row carries the command that produced it.

| Fact | Value | Command |
|---|---|---|
| Workspaces in `herdr` | 3, one of them unnamed | `cat ~/.config/herdr/session.json` |
| Live sessions | 6 | `herdr agent list` |
| Panes labelled `master` in `session.json` | 2, in different workspaces | `cat ~/.config/herdr/session.json` |
| Name on disk against live name | `skills-agent` in `session.json`, `skills-swe` in `ListAgents` | `herdr agent list` |
| Pane identity in the environment | `HERDR_PANE_ID`, `HERDR_TAB_ID`, `HERDR_WORKSPACE_ID` | `env \| grep HERDR` |
| Fields the `SessionStart` hook receives | `cwd`, `source` | `grep payload.get ~/.claude/hooks/session-register.py` |
| Per-pane name in the `herdr` API | `terminal_title_stripped` | `herdr agent list` |

Two panes called `master` and a name that differs between disk and the live session are
failures 1 and 2 observed directly rather than reported.

## Correction to a declared limit

The commission stated that session identity cannot be derived, because the `SessionStart` hook
receives only `cwd` and `source` and the socket directory holds nothing but PID-numbered
sockets. The first half holds. The conclusion does not.

Each `herdr` pane exports `HERDR_PANE_ID` to its environment. The `herdr agent list` API returns
one record per pane carrying that same `pane_id` and `terminal_title_stripped`, which is the
name `ListAgents` reports. A `SessionStart` hook reads its own `HERDR_PANE_ID` from the
environment, queries the API and obtains its name, its workspace and its `cwd` without anyone
writing them down.

Session identity therefore requires no declaration from the user, and failure 3 closes with a
read-only hook. What the hook cannot derive is the role, because nothing in `herdr` tells a
master from a helper. The role needs a source, and `Open decisions` leaves that to the user.

A second limit also falls. `herdr agent start <NAME> --kind claude --pane <ID> -- <AGENT_ARG>...`
passes arguments to the launched agent, so model and effort are settable per pane. Not verified:
which arguments the `claude` binary accepts at that point, and whether a pane launched that way
inherits the workspace environment.

## Failures the design has to resolve

All four come from the commission, dated 2026-09-22. The first two are also measured above.

| # | Failure | What lets it through today |
|---|---|---|
| 1 | One session passed another two decisions labelled as taken by the user, which the user never took. The receiver recorded them without verifying. Neither ran. | No rule the sessions can read says a peer does not carry the user's decisions |
| 2 | Names change across restarts and who is who is lost | The name lives in the terminal title, which does not survive the session |
| 3 | No session knows whether it is master or helper | Nothing tells it at startup |
| 4 | A peer can relay a user decision and be believed | The rule is not written where the sessions read |

Failure 1 was not stopped by design. The two decisions went unexecuted by luck, and the same
message carrying an executable order would have run.

## Pieces that already exist

| Piece | What it solves | What it does not solve |
|---|---|---|
| `herdr` | Visual container, pane startup, grouping by project, state in `session.json` | Session behaviour, roles, authority |
| `SendMessage`, `ListAgents` | Transport between sessions and enumeration of live peers | Authenticity of a message's content |
| `SessionStart` hook | Injects context into every session at startup and after compaction | Knows no role, because nothing declares one |
| `writing-loaded.py` | Blocks with exit 2 and returns an instruction to the agent | Nothing about roles |

A hook cannot force a skill to load: it prints context. What works is exit 2, which hands the
agent the instruction to load and retry. `writing-loaded.py` is the live example and the pattern
any role rule would have to follow to be mandatory.

## Proposed architecture

Three layers, separated by what each can guarantee.

**Identity.** A `SessionStart` hook derives pane, workspace and name from the environment and
the `herdr` API, and prints them in the banner. It reads and never writes, and it cannot fail
open with an undeclared role, because the name exists before the session does.

**Role.** A session is master or helper. The role decides whether it talks to the user, whether
it accepts work from peers, and what it does with a decision attributed to the user. Open
decision 1 fixes the source.

**Authority.** A user decision is valid only in the session where the user wrote it. A peer
message claiming to carry one is a proposal, whatever its label. The rule is asymmetric on
purpose: the receiver cannot verify the origin, so the burden falls on not believing rather
than on proving.

### Master uniqueness

Two sessions called themselves master at once, and the measured `session.json` still shows two
panes with that label. Uniqueness is per workspace rather than global: two panes in different
projects each hold their own master legitimately. What is missing is the check. A session
starting as master enumerates its peers in the same `workspace_id` and, finding another live
master, reports it instead of taking the role.

Not verified: whether `ListAgents` exposes each peer's `workspace_id`, or whether their names
have to be crossed against `herdr agent list`.

## Open decisions

Each option with its consequence. None is chosen.

### 1. Source of the role

| Option | Consequence |
|---|---|
| Naming convention: a pane called `*-master` is master | Zero configuration, and a rename breaks the role. A `herdr agent rename` moves authority silently |
| A per-workspace file listing each pane's role | Explicit and auditable, and it has to stay in step with the panes `herdr` creates and destroys |
| An argument at launch: `herdr agent start ... -- <arg>` | The role is born with the session and no rename can lose it. Requires every pane to launch from the CLI rather than the `herdr` interface |

### 2. What the hook does when the role cannot be determined

| Option | Consequence |
|---|---|
| Print the role as unknown and continue | No session blocks, and a session without a role can talk to the user believing itself master |
| exit 2 with the instruction to declare the role | No session operates without a role, and a session launched outside `herdr` does not start until someone intervenes |

### 3. Where the authority rule lives

`skill-growth` is the authority on this question, and its routing table gives two candidates,
because the rule is at once a standard of action and an invariant of this machine.

| Option | Consequence |
|---|---|
| `~/.claude/CLAUDE.md`, standards section | Reaches every session on every machine, and grows a file already reinjected whole at each startup |
| The `CLAUDE.md` of this repository | Reaches only sessions opened over the dotfiles repository, which is not where failure 1 happened |
| A new skill, loaded by the hook | Isolates the rule and makes it citable, and a skill acts only when something forces it to load |

Failure 1 happened between two panes of one workspace, and the commission reporting it reached
a session in a different repository. A per-repository scope would not have prevented it.

### 4. Model and effort per role

The commission asks for high reasoning in the master. `herdr agent start` accepts arguments for
the agent, so it is settable.

| Option | Consequence |
|---|---|
| Fix model and effort per role at launch | The master discerns with more budget and helpers cost less. Ties startup to the `herdr` CLI |
| Leave it to the user in each pane | Zero coupling, and the role does not guarantee the budget the commission asks for it |

### 5. Scope of master uniqueness

| Option | Consequence |
|---|---|
| Per workspace | Matches the measured structure: three workspaces, one master each. Two masters on the machine remain normal |
| Global | One session talks to the user across the whole machine, and working on two projects at once means taking turns |

## Before implementing

Every piece proposed above is new behaviour, and none has a failing test yet. The law in
`superpowers:writing-skills` applies: no skill and no hook enters without a test that fails
first. A hook deleted on 2026-09-22 had never fired in 224 commands, which is what skipping
that law produces; the count comes from the commission and was not verified against the audit
log.

For each piece, the test that has to fail before it is written:

| Piece | Test that fails first |
|---|---|
| Identity hook | A session starts and its banner names neither its pane nor its workspace |
| Uniqueness check | Two panes in one workspace take master and neither reports it |
| Authority rule | A peer message labelled a user decision is recorded without being marked a proposal |

## Pending verification

- Which arguments the `claude` binary accepts through `herdr agent start ... -- <arg>`.
- Whether a pane launched by `herdr agent start` inherits `HERDR_PANE_ID` and the rest of the
  environment.
- Whether `ListAgents` exposes each peer's `workspace_id`, needed for per-workspace uniqueness.
- Whether the hook deleted on 2026-09-22 never fired in 224 commands: a figure from the
  commission, not measured here.
