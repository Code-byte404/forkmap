#!/usr/bin/env python3
"""Read Claude Code session transcripts for Forkmap.

Claude Code stores each session as JSONL under
~/.claude/projects/<project-slug>/<session-id>.jsonl. The format is internal
and may change between versions, so everything here is defensive.

Usage:
  transcript.py sessions [--project DIR] [--limit N]
  transcript.py turns [--project DIR] [--session ID|current] [--from N] [--to N]
                      [--max-reply CHARS] [--out FILE]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
COMMAND_NAME = re.compile(r"<command-name>(.*?)</command-name>", re.S)
COMMAND_ARGS = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def claude_home():
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def project_dir(project):
    """Map a working directory to its transcript folder."""
    root = claude_home() / "projects"
    path = str(Path(project).resolve())
    slug = re.sub(r"[^A-Za-z0-9]", "-", path)
    if (root / slug).is_dir():
        return root / slug
    # Long paths may be truncated or hashed; fall back to a prefix match.
    for d in sorted(root.glob(slug[:80] + "*")):
        if d.is_dir():
            return d
    sys.exit(f"No transcripts found for {path} (looked in {root / slug})")


def load(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
    return entries


def text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif block.get("type") == "image":
            parts.append("[image]")
    return "\n".join(parts)


def is_human(e):
    """A message the user actually typed (not tool output or injected context)."""
    if e.get("type") != "user" or e.get("isMeta") or e.get("isSidechain") or e.get("isCompactSummary"):
        return False
    origin = e.get("origin")
    if isinstance(origin, dict) and origin.get("kind") not in (None, "human"):
        return False
    content = (e.get("message") or {}).get("content")
    if isinstance(content, list) and any(b.get("type") == "tool_result" for b in content):
        return False
    text = text_of(content).strip()
    return bool(text) and not text.startswith(("<local-command", "[Request interrupted"))


def clean_user(text):
    name = COMMAND_NAME.search(text)
    if name:  # slash command: show it the way the user typed it
        args = COMMAND_ARGS.search(text)
        return (name.group(1).strip() + " " + (args.group(1).strip() if args else "")).strip()
    return REMINDER.sub("", text).strip()


def active_branch(entries):
    """Follow parentUuid back from the last message so rewound or edited branches are skipped."""
    by_id = {e["uuid"]: e for e in entries if e.get("uuid")}
    msgs = [e for e in entries if e.get("type") in ("user", "assistant") and e.get("uuid")]
    if not msgs:
        return []
    chain, cur, seen = [], msgs[-1], set()
    while cur and cur["uuid"] not in seen:
        seen.add(cur["uuid"])
        chain.append(cur)
        parent = cur.get("parentUuid") or cur.get("logicalParentUuid")
        cur = by_id.get(parent)
    chain.reverse()
    # A broken chain (e.g. across a compaction) would drop history; fall back to file order.
    first_human = next((e for e in entries if is_human(e)), None)
    if first_human and first_human["uuid"] not in seen:
        return msgs
    return chain


def turns_of(entries):
    turns = []
    for e in active_branch(entries):
        if is_human(e):
            turns.append({"user": clean_user(text_of(e["message"]["content"])),
                          "time": e.get("timestamp", ""), "reply": []})
        elif e.get("type") == "assistant" and turns and not e.get("isSidechain"):
            t = text_of((e.get("message") or {}).get("content")).strip()
            if t:
                turns[-1]["reply"].append(t)
    return turns


def title_of(entries):
    title = ""
    for e in entries:
        if e.get("type") in ("custom-title", "ai-title", "summary"):
            title = e.get("customTitle") or e.get("aiTitle") or e.get("summary") or title
    return title


def session_files(pdir):
    return sorted(pdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def short_time(ts):
    """Transcript timestamps are UTC; show local time like the rest of the user's machine."""
    if not ts:
        return ""
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts[:16].replace("T", " ")


def cmd_sessions(args):
    pdir = project_dir(args.project)
    for p in session_files(pdir)[: args.limit]:
        entries = load(p)
        turns = turns_of(entries)
        first = turns[0]["user"].replace("\n", " ")[:60] if turns else ""
        mtime = dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{p.stem}\t{mtime}\t{len(turns)} turns\t{title_of(entries)}\t{first}")


def cmd_turns(args):
    pdir = project_dir(args.project)
    files = session_files(pdir)
    if not files:
        sys.exit(f"No sessions in {pdir}")
    if args.session in (None, "current"):
        # The running session is the one being written to right now.
        path = files[0]
    else:
        matches = [p for p in files if p.stem.startswith(args.session)]
        if not matches:
            sys.exit(f"No session starting with {args.session} in {pdir}")
        path = matches[0]
    entries = load(path)
    turns = turns_of(entries)
    lo, hi = max(args.from_, 1), min(args.to or len(turns), len(turns))
    out = [f"# session {path.stem}",
           f"# title: {title_of(entries)}",
           f"# project: {Path(args.project).resolve()}",
           f"# turns {lo}-{hi} of {len(turns)} (the last turn is usually the Forkmap request itself)",
           ""]
    for n in range(lo, hi + 1):
        t = turns[n - 1]
        reply = "\n\n".join(t["reply"])
        if args.max_reply and len(reply) > args.max_reply:
            reply = reply[: args.max_reply] + f"\n[... reply truncated, {len(reply) - args.max_reply} more chars]"
        out += [f"## Turn {n} · {short_time(t['time'])}", "[user]", t["user"], "", "[assistant]", reply or "(no text reply)", ""]
    text = "\n".join(out)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote turns {lo}-{hi} of {len(turns)} from session {path.stem} to {args.out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sessions", help="list sessions for a project, newest first")
    s.add_argument("--project", default=os.getcwd())
    s.add_argument("--limit", type=int, default=20)
    t = sub.add_parser("turns", help="print numbered turns of one session")
    t.add_argument("--project", default=os.getcwd())
    t.add_argument("--session", help="session id or prefix; default: current (most recently written)")
    t.add_argument("--from", dest="from_", type=int, default=1)
    t.add_argument("--to", type=int)
    t.add_argument("--max-reply", type=int, default=6000, help="truncate each reply to this many chars (0 = no limit)")
    t.add_argument("--out", help="write to this file instead of stdout")
    args = ap.parse_args()
    {"sessions": cmd_sessions, "turns": cmd_turns}[args.cmd](args)


if __name__ == "__main__":
    main()
