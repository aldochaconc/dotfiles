#!/usr/bin/env python3
"""PreToolUse(AskUserQuestion): a spawned pane never puts a question on screen.

A pane opened by `/spawn-sheep` carries HERDR_REPORTS_TO, and nobody is watching it: the
person who would answer is sitting in front of the master. An `AskUserQuestion` there renders a
menu in a pane the user is not looking at and the turn stops until someone finds it. Measured on
a sheep holding the written prohibition asked anyway, which is what a rule stated in
prose and enforced by nothing produces.

So the rule stops being prose. `permissionDecision: "deny"` with the reason naming what to do
instead, which is `SendMessage` to the master. A denied tool call comes back to the session as a
result it can act on, so the turn continues rather than ending: the session sends the question
where it belongs and carries on, which is what the written rule asked for and could not enforce.

Blocking only, never asking. `ask` in a pane with nobody at the keyboard is the deadlock this
hook exists to prevent, and it would arrive through the same unwatched prompt.

A pane with nothing recorded above it proceeds. Gating is opted into by a recorded recipient: a
denial and an unanswered question both stop the pane, and permitting is the outcome that keeps it
moving.

What decides is the recorded role, not `HERDR_REPORTS_TO`. That variable answers neither half of
the question: a shephrd reporting to the god carries it and is not a sheep, and a restarted pane
loses it and is not a shephrd. Measured: the gate denied every shephrd under a god
and let every restarted sheep through, the second being the failure it was written to stop.

A shephrd and a god are untouched: their questions are the ones that reach the user, and the
whole hierarchy depends on that path staying open. A shephrd running unattended is required to
batch up to four questions into one call, so denying it breaks the protocol rather than enforcing
it.

A restarted sheep is still gated, which is the half the variable lost. `herdr agent start` takes
no `--env`, so the pane comes back with `HERDR_REPORTS_TO` empty and `HERDR_PANE_ID` intact, and
the registry is what still knows a sheep is a sheep.
"""

import json
import os
import sys
from pathlib import Path

GATED = ("sheep", "watcher")
ROLES = ("god", "shephrd", "sheep", "watcher")


def _registry(env, registry_dir=None):
    """This pane's registry record, or an empty one.

    Importing `panes` is avoided, the same way `canary.py` avoids it: a hook that fails on a
    missing sibling fails on every call, and this one decides whether a question reaches a
    screen. The file is read directly and any failure gives an empty record, which reads as
    nothing recorded above this pane.
    """
    pane = (env.get("HERDR_PANE_ID") or "").strip()
    if not pane:
        return {}
    d = Path(registry_dir) if registry_dir else Path(
        env.get("HOME", "/tmp")) / ".claude" / "panes"
    try:
        return json.loads((d / (pane.replace(":", "-") + ".json")).read_text())
    except (OSError, ValueError, AttributeError):
        return {}


def role_of(env, registry_dir=None):
    """The role this pane holds, or `""` when nothing answers.

    Precedence is the registry, then the variable, matching `panes.py`, `canary.py` and
    `canary-read.py` so all four hooks read one order. `HERDR_REPORTS_TO` alone answers neither
    half: a shephrd reporting to the god has it full and is not a sheep, and a restarted pane has
    it empty and is not a shephrd.
    """
    rec = _registry(env, registry_dir)
    role = (rec.get("role") or "").strip().lower()
    if role in ROLES:
        return role
    if (env.get("HERDR_GOD") or "").strip().lower() not in ("", "0", "false", "no"):
        return "god"
    if bool(rec.get("god")):
        return "god"
    reports_to = (env.get("HERDR_REPORTS_TO") or "").strip() or (
        rec.get("reports_to") or "").strip()
    return "sheep" if reports_to else ""


REASON = (
    "AskUserQuestion is not available in this pane. This session reports to {master!r}: nobody is "
    "watching this pane and the user is in front of {master}. A question rendered here stops the "
    "turn until someone notices it.\n\n"
    "Send the decision to {master} with SendMessage instead, carrying what is blocked, the "
    "options, and what each one costs. Then stop for the turn and report. {master} resolves it, "
    "and escalates to the god only for what is genuinely beyond that tree: this is a redirection "
    "of the question, not a refusal of it.\n\n"
    "Check first that {master} appears in ListAgents: a master that is gone cannot answer, and in "
    "that one case the session addresses the user directly. shephrd-protocol holds the full rule."
)


def decision(env=None, registry_dir=None):
    """Return (permissionDecision, reason) for the current environment.

    A sheep and a watcher are gated. A shephrd and a god are not: `shephrd-protocol` requires a
    shephrd running unattended to batch up to four questions into one `AskUserQuestion`, so
    denying it forbids the mechanism the protocol mandates.

    Reading the role from `HERDR_REPORTS_TO` is wrong in both directions, measured against the
    registry. A shephrd reporting to the god has the variable full and was
    denied. A restarted pane has it empty, since `herdr agent start` takes no `--env`, so a sheep
    came back ungated: the menu opened in a pane nobody was watching, which is the failure this
    hook exists to prevent, reappearing through the restart path.

    An unresolved role permits. Nothing above this pane is recorded and no variable names a
    session above it, so there is no name to send the question to and no evidence anyone is
    waiting for it. Both outcomes of getting this wrong stop work: a denied question in an
    unwatched pane and an unanswered one both hold the pane, and permitting is the one that keeps
    it moving. Gating is opted into by a recorded recipient, never assumed.

    `attended: true` in the record releases the pane. Unattended is the default state of every
    pane and a denial here is a redirection rather than a refusal, so the flag is for the one
    case the redirection does not fit: somebody is sitting in front of this pane and wants the
    menu rendered where they are. It lives in the record rather than in a variable because
    `herdr agent start` takes no `--env`, which is the defect that produced this whole fix.
    """
    env = env if env is not None else os.environ
    rec = _registry(env, registry_dir)
    if bool(rec.get("attended")):
        return None, ""
    role = role_of(env, registry_dir)
    if role and role not in GATED:
        return None, ""

    master = (env.get("HERDR_REPORTS_TO") or "").strip() or (rec.get("reports_to") or "").strip()
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
    import tempfile

    v, r = decision({"HERDR_REPORTS_TO": "god"})
    assert v == "deny", v
    assert "god" in r
    assert "SendMessage" in r
    assert "ListAgents" in r

    # No pane and no recipient: not running under herdr, nothing to gate.
    assert decision({})[0] is None
    assert decision({"HERDR_REPORTS_TO": ""})[0] is None
    assert decision({"HERDR_REPORTS_TO": "   "})[0] is None

    # A name with surrounding whitespace is still a name.
    v, r = decision({"HERDR_REPORTS_TO": "  tess  "})
    assert v == "deny"
    assert "'tess'" in r, r

    # The four roles, from the registry. The variable is set to whatever the role implies, so a
    # gate reading it instead of the record would score every row the same and pass.
    with tempfile.TemporaryDirectory() as d:
        def record(pane, **fields):
            Path(d, pane.replace(":", "-") + ".json").write_text(json.dumps(fields))

        record("w2:p1", name="tree-a", reports_to="god", role="shephrd")
        record("w2:p2", name="worker", reports_to="lead", role="sheep")
        record("w2:p3", name="notes", reports_to="god", role="watcher")
        record("w2:p4", name="god", reports_to="", god=True, role="god")

        # A shephrd reporting to the god is not gated. Denying it forbids the batched
        # AskUserQuestion the protocol requires of a shephrd running unattended.
        assert decision({"HERDR_PANE_ID": "w2:p1",
                         "HERDR_REPORTS_TO": "god"}, d)[0] is None
        # A sheep is gated whether or not the variable survived.
        assert decision({"HERDR_PANE_ID": "w2:p2",
                         "HERDR_REPORTS_TO": "lead"}, d)[0] == "deny"
        # The case that was live: a restart empties every --env variable and the pane id
        # survives, so the registry is the only thing that still knows this is a sheep.
        v, r = decision({"HERDR_PANE_ID": "w2:p2"}, d)
        assert v == "deny", v
        assert "lead" in r, r
        # A watcher has someone above it and is gated like a sheep.
        assert decision({"HERDR_PANE_ID": "w2:p3"}, d)[0] == "deny"
        # A god is never denied: its questions are the ones that reach the user.
        assert decision({"HERDR_PANE_ID": "w2:p4"}, d)[0] is None

        # The recorded role wins over the variable in both directions.
        record("w2:p5", name="tree-b", reports_to="god", role="shephrd")
        assert decision({"HERDR_PANE_ID": "w2:p5", "HERDR_REPORTS_TO": "god"}, d)[0] is None
        # A sheep recorded with nobody above it is a contradictory record, and it proceeds: the
        # role gates, and the recipient is what a denial has to name.
        record("w2:p6", name="orphan", reports_to="", role="sheep")
        assert decision({"HERDR_PANE_ID": "w2:p6"}, d)[0] is None

        # A pane with nothing recorded above it proceeds. Gating is opted into by a recorded
        # recipient: with no name to send the question to, a denial would hold the pane on a
        # question it has no way to route. A record that is missing, malformed, or carrying a
        # value that is not a role all read the same way.
        assert decision({"HERDR_PANE_ID": "w2:pZ"}, d)[0] is None
        Path(d, "w2-p7.json").write_text("{not json")
        assert decision({"HERDR_PANE_ID": "w2:p7"}, d)[0] is None
        record("w2:p8", name="bad", reports_to="", role="nonsense")
        assert decision({"HERDR_PANE_ID": "w2:p8"}, d)[0] is None
        # A role that does not resolve still gates when a recipient is recorded beside it.
        record("w2:pB", name="odd", reports_to="lead", role="nonsense")
        assert decision({"HERDR_PANE_ID": "w2:pB"}, d)[0] == "deny"
        # A pane with no role recorded still resolves as a sheep from its recipient, which is
        # what a record written before the field existed looks like.
        record("w2:p9", name="old", reports_to="lead")
        assert decision({"HERDR_PANE_ID": "w2:p9"}, d)[0] == "deny"
        # The god flag answers where no role was recorded.
        record("w2:pA", name="g", reports_to="", god=True)
        assert decision({"HERDR_PANE_ID": "w2:pA"}, d)[0] is None
        assert decision({"HERDR_PANE_ID": "w2:pZ", "HERDR_GOD": "1"}, d)[0] is None

        # `attended` releases a pane somebody is sitting in front of, whatever its role and
        # whatever the variable says. It is the one opt-in out of the redirection.
        record("w2:pC", name="watched", reports_to="lead", role="sheep", attended=True)
        assert decision({"HERDR_PANE_ID": "w2:pC"}, d)[0] is None
        assert decision({"HERDR_PANE_ID": "w2:pC", "HERDR_REPORTS_TO": "lead"}, d)[0] is None
        # A falsy value is not an opt-in, so a field written as `false` still gates.
        record("w2:pD", name="unwatched", reports_to="lead", role="sheep", attended=False)
        assert decision({"HERDR_PANE_ID": "w2:pD"}, d)[0] == "deny"

        # The redirection names the shephrd, and says the escalation to the god is the
        # shephrd's call rather than the sheep's.
        _, r = decision({"HERDR_PANE_ID": "w2:p2"}, d)
        assert "lead" in r
        assert "god" in r

    print("ask-gate selftest passed")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
