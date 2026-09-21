# RTK

Token-optimized CLI proxy. A `PreToolUse` hook on `Bash` rewrites a covered command to its
`rtk` form; 60-90% savings on dev operations.

## Meta commands

The hook never generates these. They are the whole set worth knowing by name.

```bash
rtk gain              # Token savings summary
rtk gain --history    # Command usage history with savings
rtk discover          # Missed savings in Claude Code history
rtk proxy <cmd>       # Run a command untouched, still tracked
rtk recall --list     # Output a filter elided, by content hash
```

`rtk recall <hash>` takes the hash from a recovery hint. Without the hint, `--list` enumerates
what is stored.

## Commands the hook does not cover

A command outside the hook's table runs unfiltered, and nothing says so. `exclude_commands` in
`~/.config/rtk/config.toml` holds the deliberate exclusions, where the filter costs more than it
saves on short reads. `rtk hook check <cmd>` reports how one command would be rewritten, or that
it would not.

Writing `rtk <cmd>` by hand always works.

## Installation

```bash
rtk --version         # rtk X.Y.Z
which rtk             # ~/.local/bin/rtk, installed by bootstrap.sh
```

A `rtk gain` that fails with "command not found" while `which rtk` resolves means
reachingforthejack/rtk (Rust Type Kit) is installed instead of this one.
