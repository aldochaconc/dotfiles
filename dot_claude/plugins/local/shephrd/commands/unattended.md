---
description: Run without stopping for the user, asking the session above instead; in a god or shephrd, advance alone and batch what needs the user
argument-hint: none; what the session already has in hand is the work
allowed-tools: ["Bash", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Unattended

Tell this session the user has stepped away. What changes is who may interrupt them: exactly one
session can, and every other one asks that session instead.

The command is for a god or shephrd. A sheep is unattended from its first turn, since a spawned pane has
nobody watching it and the person who would answer sits in front of the session above; running this in a
sheep changes nothing and says so.

Load `shephrd-protocol` before acting. It holds what the mode means in each role.

## Procedure

1. **Read the role.** `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/panes.py`, which answers `role`
   directly.

   `echo "$HERDR_REPORTS_TO"` is not the same reading and fails in both directions. A restarted
   pane has the variable empty and is still a sheep: `herdr agent start` takes no `--env`, so a
   restart loses it and the registry is what survives. A shephrd has the variable full, since it
   reports to the god, and deriving from that reads it as a sheep. Measured: on
   both shapes at once.

   A sheep reports that the mode was already on and stops here.

2. **Tell the sheep.** One message each, naming that questions now arrive at this session and
   the user is not behind them. A sheep was already unattended; what it did not know is that its
   master is too, which changes what it can expect an answer to carry.

3. **Advance alone**, under the rules `shephrd-protocol` states for a god or shephrd: default what has a
   defensible default, batch what does not into one `AskUserQuestion` of up to four questions,
   and break the batch only for an irreversible decision or a blocked sheep.

4. **Report at the end of every turn**, which the protocol requires in every mode and is not
   relaxed here. Unattended means the user is not asked, not that nobody is told.

## Leaving the mode

The mode lasts until the user says so, and the user says it to the session above. A sheep never leaves
it: the pane the user came back to is not this one.
