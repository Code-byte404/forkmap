#!/usr/bin/env python3
"""Render a Forkmap data file into forkmap.html (clickable tree) and FORKMAP.md (text tree).

Usage:
  render.py [PATH_TO_forkmap.json] [--open]

Defaults to .forkmap/forkmap.json under the current directory. Both outputs are
written next to the JSON file. --open opens the HTML in the default browser.
"""
import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "tree.html"

# English defaults, using the same keys as DEF in assets/tree.html. A map's "ui" object
# overrides any of them with translated strings; {name} placeholders are filled in.
def _plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


DEFAULTS = {
    "active": "Active", "parked": "Parked", "rejected": "Rejected", "later": "Later", "pending": "Pending",
    "turn": "Turn {n}", "wait": "waiting for your pick", "scan": "scanned turns {a}–{b}",
    "nsess": lambda v: _plural(v["n"], "session", "sessions"),
    "nforks": lambda v: _plural(v["n"], "fork", "forks"),
    "nopen": lambda v: _plural(v["n"], "option", "options") + " not taken",
    "npend": "{n} waiting for your pick",
    "lq": "\u201c", "rq": "\u201d",
    # FORKMAP.md only
    "sessions": "Sessions", "tree": "Tree", "updated": "updated {t}",
    "openhtml": "Open forkmap.html for the clickable tree.",
}


def make_t(ui):
    def t(key, **v):
        s = ui.get(key, DEFAULTS[key])
        if callable(s):
            return s(v)
        for k, val in v.items():
            s = s.replace("{" + k + "}", str(val))
        return s
    return t


DOT = {"active": "🟢", "parked": "🟡", "rejected": "⚪", "later": "🔵", "pending": "○"}
OPEN = ("parked", "later", "pending")


def text_tree(data, T):
    forks = data.get("forks", [])
    sessions = data.get("sessions", {})
    multi = len(sessions) > 1
    lines = [data.get("topic") or data.get("title", "")]

    def fork_line(f):
        bits = [f"#{f['id']} {f['title']}", T("turn", n=f["turn"])]
        if multi and f.get("session") in sessions:
            bits.append(sessions[f["session"]].get("date", ""))
        if f.get("pending"):
            bits.append(T("wait"))
        return " · ".join(b for b in bits if b)

    def walk(f, prefix):
        opts = f.get("options", [])
        for i, o in enumerate(opts):
            last = i == len(opts) - 1
            bits = [f"{DOT.get(o['status'], '•')} {o['key']}. {o['name']}", T(o["status"]) if o["status"] in DEFAULTS else o["status"]]
            if o.get("summary"):
                bits.append(o["summary"])
            if o["status"] in OPEN and o.get("quote"):
                bits.append(f"{T('lq')}{o['quote']}{T('rq')}")
            lines.append(prefix + ("└─ " if last else "├─ ") + " · ".join(bits))
            child_prefix = prefix + ("   " if last else "│  ")
            kids = [c for c in forks if c.get("parent") == f"{f['id']}-{o['key']}"]
            for j, c in enumerate(kids):
                klast = j == len(kids) - 1
                lines.append(child_prefix + ("└─ " if klast else "├─ ") + fork_line(c))
                walk(c, child_prefix + ("   " if klast else "│  "))

    ids = {f"{f['id']}-{o['key']}" for f in forks for o in f.get("options", [])}
    tops = [f for f in forks if not f.get("parent") or f["parent"] not in ids]
    for i, f in enumerate(tops):
        last = i == len(tops) - 1
        lines.append(("└─ " if last else "├─ ") + fork_line(f))
        walk(f, "   " if last else "│  ")
    return "\n".join(lines)


def markdown(data, T):
    forks = data.get("forks", [])
    opts = [o for f in forks for o in f.get("options", [])]
    sessions = data.get("sessions", {})
    n_open = sum(o["status"] in ("parked", "later") for o in opts)
    n_pend = sum(o["status"] == "pending" for o in opts)
    head = " · ".join(x for x in [T("nsess", n=len(sessions)), T("nforks", n=len(forks)), T("nopen", n=n_open),
                                   T("npend", n=n_pend) if n_pend else ""] if x)
    out = [f"# {data.get('title', 'Forkmap')}", "",
           f"> {head} · {T('updated', t=data.get('updated', ''))}", f"> {T('openhtml')}", "",
           f"## {T('sessions')}", ""]
    project = data.get("project")
    for sid, s in sessions.items():
        cmd = (f'cd "{project}" && ' if project else "") + f"claude --resume {sid}"
        rng = s.get("scanned")
        scanned = T("scan", a=rng[0], b=rng[1]) if rng else ""
        out.append(f"- {s.get('date', '')} · {s.get('title', sid[:8])} · {scanned} · `{cmd}`")
    out += ["", f"## {T('tree')}", "", "```", text_tree(data, T), "```", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=".forkmap/forkmap.json")
    ap.add_argument("--open", action="store_true", help="open the HTML in the default browser")
    args = ap.parse_args()

    path = Path(args.path)
    if not path.exists():
        sys.exit(f"{path} not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["updated"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    T = make_t(data.get("ui") or {})
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__FORKMAP_DATA__", payload)
    html_path = path.with_name("forkmap.html")
    md_path = path.with_name("FORKMAP.md")
    html_path.write_text(html, encoding="utf-8")
    md_path.write_text(markdown(data, T), encoding="utf-8")
    print(f"Wrote {html_path}")
    print(f"Wrote {md_path}")

    if args.open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        try:
            subprocess.run([opener, str(html_path)], check=False)
        except FileNotFoundError:
            print(f"Could not open a browser; open {html_path} manually.")


if __name__ == "__main__":
    main()
