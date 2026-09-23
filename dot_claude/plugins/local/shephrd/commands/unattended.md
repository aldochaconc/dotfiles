---
description: Run without stopping for the user, asking the master instead; in a master, advance alone and batch what needs the user
argument-hint: none; what the session already has in hand is the work
allowed-tools: ["Bash", "Skill", "ListAgents", "SendMessage", "AskUserQuestion"]
---

# Unattended

Tell this session the user has stepped away. What changes is who may interrupt them: exactly one
session can, and every other one asks that session instead.

The command is for a master. A slave is unattended from its first turn, since a spawned pane has
nobody watching it and the person who would answer sits in front of the master; running this in a
slave changes nothing and says so.

Load `shephrd-protocol` before acting. It holds what the mode means in each role.

## Procedure

1. **Read the role.** `echo "$HERDR_AGENT_MASTER"`. Empty is a master, a name is a slave. The
   variable is read rather than the role assumed.

   A slave reports that the mode was already on and stops here.

2. **Tell the slaves.** One message each, naming that questions now arrive at this session and
   the user is not behind them. A slave was already unattended; what it did not know is that its
   master is too, which changes what it can expect an answer to carry.

3. **Advance alone**, under the rules `shephrd-protocol` states for a master: default what has a
   defensible default, batch what does not into one `AskUserQuestion` of up to four questions,
   and break the batch only for an irreversible decision or a blocked slave.

4. **Report at the end of every turn**, which the protocol requires in every mode and is not
   relaxed here. Unattended means the user is not asked, not that nobody is told.

## Leaving the mode

The mode lasts until the user says so, and the user says it to the master. A slave never leaves
it: the pane the user came back to is not this one.
