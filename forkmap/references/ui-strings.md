# UI strings

The map's fixed text defaults to English. When the output language isn't English, add a `ui` object to the map data that translates **every** key below. Keep `{placeholders}` exactly as written; they are filled in at render time. Write the strings the way a native speaker would label a UI, not word for word.

| Key | English default | Where it shows |
| --- | --- | --- |
| `active` | Active | status name |
| `parked` | Parked | status name |
| `rejected` | Rejected | status name |
| `later` | Later | status name |
| `pending` | Pending | status name |
| `turn` | Turn {n} | turn label |
| `all` | All | filter chip |
| `open` | Not taken | filter chip |
| `you` | You said | detail panel, before the user's words |
| `from` | from | detail panel, "from #1-A" |
| `wait` | waiting for your pick | after a pending fork's title |
| `scan` | Scanned turns {a}–{b} | subtitle |
| `nsess` | {n} sessions | subtitle (Claude Code) |
| `nforks` | {n} forks | subtitle |
| `nopen` | {n} options not taken | subtitle |
| `npend` | {n} waiting for your pick | subtitle |
| `pick` | Click any node to see the quote and next steps. | empty detail panel |
| `find` | Copy quote, then Cmd/Ctrl+F in chat | button |
| `cont` | Copy prompt to continue this option | button |
| `send` | Continue this option in chat | button |
| `ok` | Copied | button feedback |
| `manual` | Copy blocked, select and copy: | button fallback |
| `exp` | Expand #{id} {name} | the prompt the continue button copies or sends |
| `sess` | Session | detail panel (Claude Code) |
| `resume` | Copy command to reopen this session | button (Claude Code) |
| `hint` | The chat has no per-message links. Paste the quote into Cmd/Ctrl+F to find that turn. | detail panel footer |
| `hintCC` | Run the command in a terminal to reopen that session, then search for the quote. | detail panel footer (Claude Code) |
| `lq` / `rq` | “ / ” | quote marks around quotes and the user's words; use the language's own marks |
| `col` | ": " | separator after "You said" and "Session"; use the language's own punctuation |
| `sessions` | Sessions | FORKMAP.md heading (Claude Code) |
| `tree` | Tree | FORKMAP.md heading (Claude Code) |
| `updated` | updated {t} | FORKMAP.md summary line (Claude Code) |
| `openhtml` | Open forkmap.html for the clickable tree. | FORKMAP.md summary line (Claude Code) |

English plurals ("1 fork" / "2 forks") are handled automatically; a translation is a single string with `{n}`, so pick a form that reads well for any count.
