---
name: forkmap
description: Draws the options that were set aside in the current conversation as a clickable tree (a "fork map"). When an earlier reply offered several parallel approaches, directions, angles or paths and the conversation then followed only one, find those fork points and mark each option's status (active / parked / rejected / later), the turn it appeared in, and its original wording. Use this skill whenever the user asks, in any language, what other directions or options came up earlier, which alternatives were skipped, what the unchosen ones were, or asks for a fork map, e.g. "what other options did we skip" or "what were the alternatives you mentioned earlier", even if they never say "Forkmap". Also use it when the user wants to change an option's status, see only some options, or export as Markdown/Mermaid.
---

# Forkmap

In a long conversation, an early reply often lists several directions, only one gets explored, and the rest sink out of sight. To get them back the user has to scroll all the way up. Your job is to do that scrolling for them: scan the current conversation, find every fork point, and draw the roads not taken, with their locations, as a clickable tree.

The tree is only worth something if it is **trustworthy** and **locatable**. The user will use it to go back to the original text and pick up a direction, so leave out a doubtful fork rather than invent options, and make sure every option can be found in the original text.

## Output language

Everything you produce (the map's UI, topic, fork titles, summaries, the chat reply, the text tree, exports) is in **the language the user has been using in this conversation**: if they've been chatting in English, output English; if in Japanese, output Japanese; likewise for any language.

- Judge by the user's messages in the conversation, not by the invocation message. The invocation may be just "/forkmap" or a short phrase, and the user may trigger it in a different language out of habit.
- If the user mixed languages, go with the language most of their messages are in.
- `quote` and `turns` are always verbatim, so they stay in whatever language the original text was in. Never translate them, or Cmd/Ctrl+F won't find them.
- The examples in this file are in English for illustration only. Don't let them pull the output into English when the conversation is in another language.

## Where you are running

- **Claude Code** (you have a shell, and `~/.claude/projects/` exists): read `references/claude-code.md` in this skill's directory now and follow it. It replaces steps 1 and 5 below with reading the local transcript and saving the map per project across sessions. Steps 2–4 still apply.
- **Claude App** (claude.ai, desktop or mobile): follow the steps below as written.

## Step 1: Number the turns

Count from the start of the conversation. Each user message is one turn; "turn N" means the user's Nth message plus the reply to it. The message that invoked Forkmap is not analyzed and not counted.

**Read every turn, up to the last one before the invocation.** The most recent turn is the easiest to miss: it is closest to the invocation and looks "still in progress", yet it is often exactly what the user wants to see. Record the scanned range (e.g. turns 1–3); the page displays it so the user can confirm at a glance that nothing was skipped.

If earlier parts of the conversation have been compacted or summarized and you can't see the original text, say which part you can't see and organize only what you can see. Don't guess original wording from a summary.

## Step 2: Find the fork points

A fork point must meet both conditions:

1. **Parallel options**: a reply (usually the assistant's, but a list the user wrote also counts) offers two or more mutually substitutable approaches, directions, angles, structures or paths.
2. **The conversation narrows**: afterwards the conversation continues along only one (or a few) of them; the others are not developed.

These are **not** fork points:

- Sequential steps (step 1, step 2…). They are all meant to be done, not chosen between.
- Examples, pros-and-cons lists, lists of caveats.
- Option sets where every option was later adopted or discussed.
- The same idea phrased differently.

One special case: **options that were just listed and the user hasn't picked yet**. For example, the latest reply offered a few directions and the user immediately invoked Forkmap, or only replied "ok" / "continue". The conversation hasn't narrowed, but the fork still goes in the tree, otherwise the user will think that turn was missed. Mark the fork `"pending": true` and give its options the status `pending`. Don't mark them parked: they are "not chosen yet", not "set aside".

Pending applies **only to the last turn before the invocation**. If the user sent any further message after a list without picking from it (asked something else, moved to the next question), the conversation has moved on: that fork is a normal fork and its unpicked options are `parked`. So at most one fork, the latest, can be pending.

When unsure, ask yourself: "Would the user later want to come back and say 'what about that other direction?'" If yes, include it; if no, leave it out.

Nesting: if a new fork appears inside one of the options, record it as a separate fork point and note which option it hangs under (e.g. `1-A`). The tree draws it as a child of that option.

## Step 3: Decide each option's status

Judge from actual evidence in the conversation:

| Code | Label | Evidence |
| --- | --- | --- |
| `active` | Active | The conversation went on to develop it, or the user explicitly chose it |
| `rejected` | Rejected | The user or assistant explicitly ruled it out, usually with a reason |
| `later` | Later | The user said something like "come back to this later", "park it for now", "might be useful later" |
| `parked` | Parked | Not chosen, not explicitly rejected or flagged; just never mentioned again |
| `pending` | Pending | Only for the not-yet-picked fork described above. Shown as a hollow gray dot and not counted as "not taken" |

When evidence is thin, use `parked`, the least presumptuous status. `later` needs the **user** to have deferred it; if only the assistant suggested "do this later" and the user moved on without answering, it is `parked`. Use `rejected` only if you can point to the sentence that rejected it.

Wherever you write a status out (reply, text tree, Markdown, Mermaid), use its label in the output language. When the output language isn't English, take the labels from the `ui` object you build in step 4, so text output matches the page word for word.

## Step 4: Build the data

Put the result in this JSON:

```json
{
  "title": "Forkmap · Personal finance app stack",
  "topic": "Personal finance app stack",
  "lang": "en",
  "scanned": [1, 10],
  "turns": {"3": "Where should the backend store", "8": "What ORM goes with Postgres"},
  "forks": [
    {
      "id": "1",
      "title": "Database choice",
      "turn": 3,
      "parent": null,
      "summary": "Picking storage for the ledger data",
      "quote": "Here are four databases to consider",
      "options": [
        {"key": "A", "name": "PostgreSQL", "status": "active", "turn": 3,
         "summary": "Adopted, designing the schema", "quote": "PostgreSQL is the default for relational data"},
        {"key": "C", "name": "MongoDB", "status": "rejected", "turn": 3,
         "summary": "Turn 5: you said the data is strongly relational", "quote": "MongoDB if the shape keeps changing"}
      ]
    },
    {"id": "2", "title": "ORM choice", "turn": 8, "parent": "1-A", "quote": "...", "options": ["..."]}
  ]
}
```

- `title`, `topic`: follow the naming rules below. Don't rename on each run.
- `lang`: the output language as a BCP 47 code (`"en"`, `"zh"`, `"ja"`, `"es"`…). Write `topic`, fork titles and `summary` in that language. Option `name`s keep the original reply's wording.
- `ui`: only when the output language isn't English. The template's fixed text (buttons, status names, "Turn 8 · You said", filter chips) is English; translate it by adding a `ui` object with every key listed in `references/ui-strings.md`, written naturally in the output language. Keep `{placeholders}` as they are. If this conversation already produced a map, reuse its `ui` unchanged so the wording never shifts between runs.
- `scanned`: first and last turn scanned. The last is the final turn before the invocation.
- `turns`: for every turn that appears in the tree, the verbatim opening of the user's message in that turn (20 characters max), skipping attachment placeholders such as `[Image #2]` so the snippet is the user's actual words. The app doesn't show turn numbers, so when the user opens a node they see "Turn 8 · You said: 'What ORM goes with Postgres'". Their own words are easier to recognize while scrolling up.
- `forks[].id`: number forks 1, 2, 3… in order of appearance. `parent` is the option it hangs under (`"1-A"`), or `null` for top-level forks.
- `forks[].pending`: `true` for the fork the user hasn't picked from yet; omit otherwise.
- `options[].key`: a letter. `name` keeps the wording of the original reply so the user can match them up. When the options were written as prose rather than a list, a short faithful label is fine; `name` doesn't need to be verbatim, because `quote` is what the user searches for.
- `summary`: what the option is and why it has its current status. For active, say how it's progressing; for rejected, the reason and turn; for parked, where it would fit.
- `quote`: a **verbatim** excerpt of 25 characters or fewer from the original text. The Claude App chat page has no per-message links, so the user finds the turn by pasting this into Cmd/Ctrl+F. It must be a string that really exists in the text, as distinctive as possible, never paraphrased. A fork's `quote` is a distinctive verbatim span from the reply that introduced the options, ideally from the sentence that sets them up; if that sentence is longer than 25 characters, take a span of it.

### Naming rules

The user looks for this map in the artifact list and across repeated runs. If the title changes every time, they can't find it. So the title must be fixed and predictable:

- `topic` comes from **the subject of the user's turn-1 message**, condensed into a short noun phrase (about 6 words; about 12 characters in languages written without spaces), written in the output language. Look only at turn 1 and don't switch because the conversation drifted later; that way the same conversation always yields the same name.
- `title` is always `Forkmap · {topic}`, in every language. The prefix never changes, so searching "Forkmap" in the artifact list finds every map.
- If a fork map **has already been produced in this conversation**, reuse its `title` and `topic` exactly, even if you think of a better name.
- The artifact's title matches `title`.

## Step 5: Render the tree

Use code execution to read `assets/tree.html` from this skill's directory. Replace `__FORKMAP_DATA__` with the JSON from step 4 (the JSON must not contain `</script>`), then output the full HTML as an HTML artifact titled with `title`. If this conversation already has a fork-map artifact, **update that one** instead of creating a new one, so the conversation has one map and its history stays in one place. Don't change the template's structure or styling, only the data, so the map looks the same every time and the user never has to re-learn it.

What the template does on its own (you only supply data): the root is the conversation topic, forks hang under it, options under forks, and nested forks under their option. Colors mark status (green = active, yellow = parked, gray strikethrough = rejected, blue = later, hollow gray = pending). Forks with nothing left untaken or pending start collapsed; everything else is shown, and the user can narrow it with the filter chips. Clicking a node shows its status, turn, what the user said in that turn, the summary, the quote, and buttons to copy the quote and to continue that direction.

Keep the chat reply to two sentences, in the output language. For example: "Scanned turns 1–10: 3 forks, 4 options not taken. Click a node to copy its quote and find it with Cmd/Ctrl+F; to pick one up, say 'expand #1-B'." With a pending fork, add: "You haven't picked from the options in turn 10 yet, so they're marked pending." In another language, write the same two sentences naturally in that language.

**Don't put any quotes in the chat reply**, and don't repeat the list. A quote in the reply becomes an extra Cmd/Ctrl+F match and gets in the way of finding the original.

**If the template can't be read** (code execution off, file not found), fall back to a text tree in a code block with the same hierarchy:

```
Forkmap · Personal finance app stack (scanned turns 1–10)
└─ #1 Database choice · Turn 3
   ├─ 🟢 A. PostgreSQL · Active · adopted, designing the schema
   │  └─ #2 ORM choice · Turn 8
   │     ├─ 🟢 A. Prisma · Active
   │     └─ 🟡 B. Drizzle · Parked ·"Drizzle stays close to raw SQL"
   ├─ 🟡 B. SQLite · Parked ·"SQLite is simplest for a prototype"
   ├─ ⚪ C. MongoDB · Rejected · ruled out in turn 5, data is relational
   └─ 🔵 D. DuckDB · Later ·"DuckDB is fast for analytics"
```

The first line carries `title` and the scanned range. Untaken options (parked, later) include their verbatim quote so the user can search for it; active and rejected ones can skip it. Pending options use ○, and the fork title gets "· waiting for your pick" (translated to the output language). All labels and fixed phrases are translated; quotes stay verbatim.

If the conversation has no fork points, say so and briefly explain why (e.g. it has been a single line of discussion). Don't force a tree.

## Follow-ups

The user may phrase these in any language; recognize the intent.

- **Change a status**: when the user says something like "mark B as rejected", change it as told and render the tree again. The user's judgment overrides your inference.
- **Filter**: when the user says something like "only show parked ones", still render the full map and name the parked options in the reply (the user can also click the filter chips in the map).
- **Expand an option**: when the user says something like "expand #1-B", go back to where it was said and continue that direction using that context plus what has been learned since, and change its status to active.
- **Run again**: in the same conversation, keep the earlier title, numbering and any statuses the user changed by hand; only append new forks, and update the existing artifact, so names and numbers the user remembers don't shift. If a previously pending fork has since been picked from, give its options normal statuses and drop `pending`.

## Export

- Markdown: write the text tree to `forkmap.md` for download (with no code execution, just output it in the reply).
- HTML file: save the filled-in page as `forkmap.html` for download; it opens in a browser with a double-click.
- Mermaid: output a `flowchart LR` with the same structure, coloring by status with `classDef` (active green, parked yellow, rejected gray, later blue, pending gray outline). Avoid double quotes and square brackets in node text so it parses.
