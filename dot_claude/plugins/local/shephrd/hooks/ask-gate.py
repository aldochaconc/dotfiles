#!/usr/bin/env python3
"""PreToolUse(AskUserQuestion): a spawned pane never puts a question on screen.

A pane opened by `/spawn-agent` carries HERDR_REPORTS_TO, and nobody is watching it: the
person who would answer is sitting in front of the master. An `AskUserQuestion` there renders a
menu in a pane the user is not looking at and the turn stops until someone finds it. Measured on
2026-09-22: a sheep holding the written prohibition asked anyway, which is what a rule stated in
prose and enforced by nothing produces.

So the rule stops being prose. `permissionDecision: "deny"` with the reason naming what to do
instead, which is `SendMessage` to the master. A denied tool call comes back to the session as a
result it can act on, so the turn continues rather than ending: the session sends the question
where it belongs and carries on, which is what the written rule asked for and could not enforce.

Blocking only, never asking. `ask` in a pane with nobody at the keyboard is the deadlock this
hook exists to prevent, and it would arrive through the same unwatched prompt.

A master has HERDR_REPORTS_TO empty and is untouched: its questions are the ones that reach
the user, and the whole hierarchy depends on that path staying open.
"""

import json
import os
import sys

REASON = (
    "AskUserQuestion is not available in this pane. HERDR_REPORTS_TO is set to {master!r}, so "
    "this session is a sheep: nobody is watching this pane and the user is in front of {master}. "
    "A question rendered here stops the turn until someone notices it.\n\n"
    "Send the decision to {master} with SendMessage instead, carrying what is blocked, the "
    "options, and what each one costs. Then stop for the turn and report. Check first that "
    "{master} appears in ListAgents: a master that is gone cannot answer, and in that one case "
    "the session addresses the user directly. shephrd-protocol holds the full rule."
)


def decision(env=None):
    """Return (permissionDecision, reason) for the current environment.

    A sheep is any session with a non-empty HERDR_REPORTS_TO. Whitespace is not a name, so it
    reads as empty: a variable set to a blank string comes from a spawn that could not resolve a
    name, and treating that as a master is what the spawn command already refuses to do.
    """
    env = env if env is not None else os.environ
    master = (env.get("HERDR_REPORTS_TO") or "").strip()
    if not master:
        return None, ""
    return "deny", REASON.format(master=master)


def main():
    # The payload is read and discarded: the verdict depends on which pane this is, never on what
    # the question says. A hook that read the question would be deciding whether it is a good
    # question, which is the master's job and not this one's.
    try:
        sys.stdin.read()
    except Exception:
        pass

    verdict, reason = decision()
    if verdict is None:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": verdict,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def selftest():
    v, r = decision({"HERDR_REPORTS_TO": "os-master"})
    assert v == "deny", v
    assert "os-master" in r
    assert "SendMessage" in r
    assert "ListAgents" in r

    assert decision({})[0] is None
    assert decision({"HERDR_REPORTS_TO": ""})[0] is None
    assert decision({"HERDR_REPORTS_TO": "   "})[0] is None

    # A name with surrounding whitespace is still a name.
    v, r = decision({"HERDR_REPORTS_TO": "  tess  "})
    assert v == "deny"
    assert "'tess'" in r, r

    print("ask-gate selftest: 8 checks passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
