#!/usr/bin/env python3
"""SessionStart(startup|resume|clear|compact): inject the Speaking and a banner.

Two jobs:
  1. Extract the `Speaking` section from ~/.claude/CLAUDE.md and print it, so the
     rules reach context even when the memory file does not load, and again after every
     compaction.
  2. Print an inventory banner and instruct the model to reproduce it, so a failed load
     is visible instead of silent.

The rules are read from CLAUDE.md at runtime and never copied here: one source, no drift.
A missing file or section is reported as a failure in the banner.

Self-check: python3 session-register.py --selftest
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
CFG = HOME / ".claude"
SECTION = "# Replying"


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {} if default is None else default


def extract_rules(md_path=None):
    """Return (text, line_count, error). error is None on success."""
    md = md_path or (CFG / "CLAUDE.md")
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return "", 0, f"{md} no se pudo leer"
    m = re.search(r"(?m)^" + re.escape(SECTION) + r"[ \t]*$", text)  # a heading, not a mention in a table
    if m is None:
        return "", 0, f"sección '{SECTION}' ausente en {md}"
    rest = text[m.end():]
    nxt = rest.find("\n# ")
    body = SECTION + (rest if nxt == -1 else rest[:nxt])
    body = body.rstrip() + "\n"
    return body, body.count("\n"), None


def open_findings(root):
    """(count, oldest ISO date) from the Log table of the `writing` skill, or (None, None).

    A row in that log is an open finding: a defect observed with no rule yet. Closed rows
    leave the table, so the count is the length of the working list and the oldest date is
    how long the front of it has waited. Read at session start because a log nobody opens
    stops being a list and becomes an archive.
    """
    log = Path(root) / "skills" / "writing" / "SKILL.md"
    try:
        text = log.read_text(encoding="utf-8")
    except OSError:
        return None, None
    if "## Log" not in text:
        return None, None
    rows = [l for l in text[text.index("## Log"):].split("\n")
            if re.match(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|", l)]
    if not rows:
        return 0, None
    dates = sorted(l.split("|")[1].strip() for l in rows)
    return len(rows), dates[0]


def names(pattern, root, depth_file="SKILL.md"):
    """Skill dirs (root/*/SKILL.md) or agent files (root/*.md)."""
    if not root.is_dir():
        return []
    if pattern == "skills":
        return sorted(d.name for d in root.iterdir() if (d / depth_file).is_file())
    return sorted(f.stem for f in root.glob("*.md"))


def plugin_inventory():
    settings = read_json(CFG / "settings.json")
    enabled = [k for k, v in (settings.get("enabledPlugins") or {}).items() if v is True]
    installed = read_json(CFG / "plugins" / "installed_plugins.json").get("plugins") or {}
    rows = []
    for key in sorted(enabled):
        entries = installed.get(key) or []
        count = 0
        for e in entries:
            skills = Path(e.get("installPath", "")) / "skills"
            if skills.is_dir():
                count += len(list(skills.glob("*/SKILL.md")))
        rows.append((key.split("@")[0], count))
    return rows, settings


def flag(name, default="ausente"):
    try:
        return (CFG / name).read_text(encoding="utf-8").strip() or default
    except OSError:
        return default


def build_banner(cwd, rules_lines, rules_error):
    plugins, settings = plugin_inventory()
    proj = Path(cwd) / ".claude" if cwd else None
    lines = []
    ok = rules_error is None
    lines.append("SESION INICIALIZADA  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    if ok:
        lines.append(f"  reglas de habla: OK, {rules_lines} lineas desde ~/.claude/CLAUDE.md")
    else:
        lines.append(f"  reglas de habla: FALLO, {rules_error}")
    lines.append(f"  caveman: {flag('.caveman-active')}   ponytail: {flag('.ponytail-active')}")

    hooks = read_json(CFG / "settings.json").get("hooks") or {}
    events = ", ".join(f"{k}({len(v)})" for k, v in hooks.items()) or "ninguno"
    lines.append(f"  hooks de usuario: {events}")
    check = CFG / "hooks" / "register-check.py"
    lines.append(f"  verificacion de markdown: {'activa' if check.is_file() else 'AUSENTE'}")

    us = names("skills", CFG / "skills")
    ua = names("agents", CFG / "agents")
    lines.append(f"  skills de usuario ({len(us)}): {', '.join(us) or 'ninguna'}")
    lines.append(f"  agentes de usuario ({len(ua)}): {', '.join(ua) or 'ninguno'}")

    if proj and proj.is_dir():
        ps = names("skills", proj / "skills")
        pa = names("agents", proj / "agents")
        lines.append(f"  skills del proyecto ({len(ps)}): {', '.join(ps) or 'ninguna'}")
        lines.append(f"  agentes del proyecto ({len(pa)}): {', '.join(pa) or 'ninguno'}")
        n, oldest = open_findings(proj)
        if n is None:
            lines.append("  hallazgos abiertos: sin log de writing")
        elif n == 0:
            lines.append("  hallazgos abiertos: ninguno")
        else:
            age = (datetime.now().date() - datetime.strptime(oldest, "%Y-%m-%d").date()).days
            lines.append(f"  hallazgos abiertos: {n}, el mas viejo hace {age} dias ({oldest})")

    total = sum(c for _, c in plugins)
    detail = ", ".join(f"{n}:{c}" for n, c in plugins) or "ninguno"
    lines.append(f"  plugins activos ({len(plugins)}, {total} skills): {detail}")
    mcp = ", ".join((settings.get("mcpServers") or {}).keys()) or "ninguno"
    lines.append(f"  MCP en settings: {mcp}")
    lines.append(f"  modelo: {settings.get('model', 'por defecto')}   esfuerzo: {settings.get('effortLevel', 'por defecto')}")
    return "\n".join(lines), ok


LOG = CFG / "hooks" / "session-register.log"


def log_run(source, cwd, count, err):
    """Leave evidence on disk, so 'did the hook fire' is a file check."""
    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    state = f"OK:{count}" if err is None else f"FALLO:{err}"
    line = (f"{stamp} source={source or '?'} cwd={cwd or '?'} rules={state} "
            f"caveman={flag('.caveman-active')} ponytail={flag('.ponytail-active')}\n")
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass
    return line


def main():
    payload = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    cwd = payload.get("cwd") or ""
    source = payload.get("source") or ""

    rules, count, err = extract_rules()
    banner, ok = build_banner(cwd, count, err)
    log_run(source, cwd, count, err)

    print("INSTRUCCION PRIORITARIA: reproducir el bloque SESION INICIALIZADA de abajo, "
          "completo y en un bloque de codigo, al comienzo de la primera respuesta de "
          "esta sesion, antes de cualquier otro contenido. No se vuelve a mencionar en "
          "las respuestas siguientes.")
    if not ok:
        print("INSTRUCCION: las reglas de habla no cargaron. Declararlo en la primera "
              "respuesta antes del banner.")
    print()
    print(banner)
    print()
    if rules:
        print("Reglas de habla vigentes, reinyectadas en cada sesion y despues de "
              "cada compactacion:\n")
        print(rules)
    return 0


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        good = Path(d) / "good.md"
        good.write_text("# A\n\ntexto\n\n# Replying\n\nr1\nr2\n\n# Z\n\nfin\n")
        body, n, err = extract_rules(good)
        assert err is None, err
        assert body.startswith("# Replying"), body
        assert "r1" in body and "r2" in body, body
        assert "# Z" not in body and "# A" not in body, body
        assert n == 4, n

        tail = Path(d) / "tail.md"
        tail.write_text("# Replying\n\nsolo esto\n")
        body, n, err = extract_rules(tail)
        assert err is None and "solo esto" in body, (err, body)

        missing = Path(d) / "missing.md"
        missing.write_text("# Otra\n\nnada\n")
        _, _, err = extract_rules(missing)
        assert err and "ausente" in err, err

        _, _, err = extract_rules(Path(d) / "nope.md")
        assert err and "no se pudo leer" in err, err

    banner, ok = build_banner("", 93, None)
    assert "SESION INICIALIZADA" in banner and ok, banner
    assert "reglas de habla: OK" in banner, banner
    banner, ok = build_banner("", 0, "sección ausente")
    assert not ok and "FALLO" in banner, banner
    print("selftest ok")


def show_log(n=15):
    """Print the last n recorded runs, or say the hook has never fired."""
    try:
        lines = LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        print(f"{LOG} no existe: el hook nunca corrio.")
        return 1
    if not lines:
        print(f"{LOG} esta vacio: el hook nunca corrio.")
        return 1
    print(f"{len(lines)} ejecuciones registradas. Ultimas {min(n, len(lines))}:")
    for line in lines[-n:]:
        print("  " + line)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    if "--check" in sys.argv:
        sys.exit(show_log())
    sys.exit(main())
