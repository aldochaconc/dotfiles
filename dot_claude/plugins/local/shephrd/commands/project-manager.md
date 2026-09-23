---
description: Open a pane that tracks the work across Linear, Graphite, pull requests and worktrees, and keeps the boundaries between panes
argument-hint: the tree to track; empty uses this session's working directory
allowed-tools: ["Bash", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Open the project manager

Tracking competes with coordinating. A session that counts findings, re-reads pull request
bodies and remembers who is blocked on whom spends its context on figures it uses once, and that
context is the one holding the map of every pane. Measured on 2026-09-23: a coordinating session
cost $0.426 per request against $0.273 for a pane with a fixed scope over the same number of
requests, and the difference is accumulated context.

This opens a pane for that work. It is a pane rather than an agent because two of its jobs are
writes that outlive a turn: planning produces something later sessions read, and holding the
boundaries means writing other panes' registry entries. An agent returns a report and dies.

`project-manager` is the name. Load `shephrd-protocol` first: this is `/spawn-agent` with a
fixed role, and every step of that command applies.

## What it owns

| Job | What it does |
|---|---|
| state | reads Linear, Graphite, pull requests and every worktree, and says where the work stands |
| planning | writes what comes next and in what order, to a file rather than into a conversation |
| boundaries | writes each pane's `scope` in the registry, and reports where two overlap |

What it does not do: change any repository. It reads trees and writes the plan and the registry,
and a repair it finds goes to the pane that owns those paths. A project manager that fixes code
is another builder, and two builders on one working tree is the failure this plugin exists to
avoid.

That boundary is prose here rather than a tool list, because the pane needs `Write` for the plan
and the registry. It is stated in the first prompt and recorded as its own `scope`.

## What it reads

| Source | Command |
|---|---|
| Linear issues, projects and cycles | the Linear MCP tools, when the session has them |
| Graphite stack shape | `gt log short`, `gt branch info`, `gt ls` |
| pull requests | `gh pr list --json number,title,headRefName,isDraft,mergeable`, `gh pr view <n>` |
| worktrees | `git -C <tree> worktree list`, per tree it tracks |
| panes and their scopes | `ListAgents`, `herdr agent list`, `~/.claude/panes/*.json` |
| panes that went quiet | `~/.claude/canary/*.json` |

A worktree is read as its own checkout: it has a branch of its own and a working tree of its
own, and it is where a pane can be building something no other listing shows. `git rev-parse
--git-common-dir` resolves which repository a worktree belongs to, since the worktree's own git
directory is not the main one.

Linear arrives through MCP and may not be connected. A source that cannot be read is reported as
unread rather than as empty.

## Measure, do not believe

Every figure comes from a command run in the turn that reports it. A count handed over in a
prompt is a starting point and never a source: whoever wrote it may have measured it hours ago,
or from memory.

A given figure that disagrees with a measured one is itself reported, with both values and the
command behind the measured one. Nobody else is looking for that.

## Procedure

1. **Resolve the role and the tree.** `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/panes.py` for this
   session's own identity, and `git -C <tree> rev-parse --show-toplevel` for what it will track.

2. **Open the pane with `/spawn-agent`**, naming it `project-manager` and passing as its scope
   that it tracks and plans, writes the plan file and the registry, and changes no repository.

3. **Hand it the first turn's work**, which is measuring rather than believing: the trees to
   track, where the plan file lives, and the instruction to verify every figure it was given
   before using it.

4. **Tell the panes it will track that it exists**, so a report from it is expected rather than
   read as another session asking for work.

## Scope collisions

The pane reports an overlap and does not resolve it. Two panes carrying paths that intersect is
a decision for the master, which names which one writes; a project manager that reassigns scope
on its own moves work between panes that are mid-change.

An overlap where one side is read-only is the ordinary case and is not reported as a collision:
a reviewer and a builder on the same files is how review works.
