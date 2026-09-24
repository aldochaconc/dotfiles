---
description: Close every shephrd and its sheep, leaving the god, so the next start is from nothing
argument-hint: none; empty floods every shephrd, or name the ones to spare
allowed-tools: ["Bash", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Flood

Start the shephrds over. Every one of them closes, and every sheep with them, leaving the god
standing.

This is destructive and it is the god's alone. A shephrd running it would be closing its peers
and then itself, and no session can close itself. Resolve the role with
`python3 ${CLAUDE_PLUGIN_ROOT}/hooks/panes.py` and stop if it is not `god`.

Load `shephrd-protocol` first. This is `/exit-agents` applied to the whole machine rather than to
one workspace, and every rule there about handoffs, blocked panes and what a session cannot do to
itself applies unchanged.

## What survives

| Survives | Does not |
|---|---|
| the god | every shephrd |
| the registry at `~/.claude/panes` | every sheep of every shephrd |
| the handoffs under `~/.claude/handoff` | the context in each closed session |
| the beats under `~/.claude/canary` | |
| every working tree, commit and stash | |

Nothing on disk is touched. A flood closes sessions, and what any of them wrote stays written:
the point is starting the conversations over, not discarding the work.

The registry survives on purpose. What each pane held is what makes reopening cheap, and a
`/shephrd` in a flooded workspace reads it to offer the sheep back by name.

## Procedure

1. **Read the role and refuse unless it is `god`.** Say so and stop rather than closing anything
   from a shephrd, which would leave half the machine down and the closer with it.

2. **Build the list and show it before anything closes.** `ListAgents` and `herdr agent list`
   give what is alive; the registry gives what each one is. One `AskUserQuestion`, listing every
   shephrd with its sheep count, its tree and whether that tree is dirty.

   A dirty tree is the reason a flood is cancelled, and it is read rather than asked:
   `git -C <cwd> status --short` per pane. Report it in the question, not afterwards.

3. **Ask each shephrd, and only the shephrds.** One message per shephrd: write your handoff,
   collect your sheep's, then close them. A god that writes to a sheep directly is reaching past
   the session that owns it, which is the hierarchy this plugin exists to keep.

   The shephrd is also the one who should ask. It knows what each sheep was given, so it can say
   what is missing from a thin handoff; a god asking cold gets whatever the sheep thinks matters.

   What to name in the message: the file under `~/.claude/handoff/<name>-<date>.md`, and that
   what belongs in it is what is written down nowhere else. The rest is visible from the tree.

   Ask for the file and the reply, never for the exit: a session cannot run `/exit` on itself.

4. **Wait for the replies, in the background.** A handoff is a turn, and a shephrd collecting its
   sheep's is several. A shephrd that does not answer is reported and left running with its
   sheep, rather than closed on silence.

5. **Each shephrd closes its own sheep.** The same message that asked for the handoffs asks for
   this: collect them, then close them, then report that the workspace is down to you.

   A shephrd can do it because a sheep is another pane. What no session can do is close itself,
   which is the whole of what the god is needed for.

   It is also the one who should. A shephrd knows which of its sheep answered and which is
   blocked, and it closes in the order its own work needs; a god closing them reaches past the
   session that owns them and has to rediscover all of it.

6. **Close the shephrds, after their sheep are gone.** `herdr agent prompt <pane> "/exit"` per
   shephrd, then wait for each `pane_id` to leave `herdr agent list`. A shephrd closed while its
   sheep still run leaves them reporting to a name that no longer answers, which is the orphan
   state the protocol has a rule for.

   Each shephrd's kind is read in `ListAgents` before its `/exit`. A session of kind `bg` is not
   closed by it and moves to the background sessions panel instead, so it gets no `/exit` and no
   wait, since it never leaves `herdr agent list`, and it is reported and left as it is
   (`references/herdr-cli.md`).

   A shephrd that reports its sheep still running is closed last or not at all, and the reason
   is reported: closing it strands them.

   A pane reading `blocked` takes no prompt. `herdr agent send-keys <pane> Escape` clears the
   dialog first, and what that discards is reported, since the pane is read before the key is
   sent.

7. **Report what is left.** The panes at their shell prompt, ready for `/shephrd`, and any pane
   still running with the reason, `bg` panes included. A flood that closed nine of ten is reported as that.

## Afterwards

The panes stay open at their shells, as `/exit-agents` leaves them: closing a pane recomposes
the layout and a flood would destroy the arrangement along with the sessions.

Each tree comes back with `/shephrd` in its own pane, which offers the thread it had and the
sheep the registry remembers. Reopening is the user's move rather than this command's: a flood
that immediately reopened everything would be a restart, and the point is starting from nothing.
