# Setter objection check (daily): runbook

Owner: Sheila Xu (sheila@smbdealhunter.xyz). Set up Oct 25, 2026. Setters: Bali (Jabali Dumas), Jordan Kempster, Jose Rodriguez.

How well each setter handled objections on their real conversations, graded against the objection section of the "Setter Inbound Call Script_Oct 2026" (the Welcome Series Outbound SOP, Step 4, points there). It is its own routine, separate from Bali's scorecard and from the "Setter handoff check" task (Sheila, Oct 25).

It has two outputs (Sheila, Oct 26), both claude.ai dashboards owned by Sheila:

| Page | Link | What it is |
| --- | --- | --- |
| **Setter objection check** (the daily scorecard) | https://claude.ai/artifact/9nqQgbts5j9irENWwd8jHv | For leadership. A day picker (opens on the latest day), a one-line summary, one card per setter (% handled per script, Hit / Partial / Miss, dials, conversations, objections, set live), coaching focus per setter, by-objection table, flags. A setter-facing version comes later |
| **Setter objection library** | https://claude.ai/artifact/Nwx2mFK9aRraL9MMW3JvRS | The growing record of every graded objection since Oct 23: by-objection totals for all days, and a searchable table (date range, setter, objection, grade, set to closer) with the lead's words, the grade, what decided it and what to do instead per the script |

Both read attached JSON files. Each run adds the new day's rows to those files (a rerun replaces that day). The pages themselves don't change day to day.

## Rules

- Read-only everywhere except the two dashboards above: never write to Close, never post to Slack, never message a setter. Sheila shares the pages herself.
- Never commit call content, grades or reports to the repo (lead details). They live only on the two dashboards.
- Close data and recordings come through the Composio remote workbench (`proxy_execute`, `close` toolkit). Close has no transcripts and won't turn them on (Sheila, Oct 25): we transcribe the recordings ourselves with faster-whisper (the workbench collects, the Claude container transcribes; see Files).
- Only recordings of 60+ seconds are transcribed (Sheila, Oct 25). Voicemails, screeners and logistics calls are skipped at grading.
- Grading follows `RUBRIC.md`. Don't change the rubric, the 60-second floor or the pages' layout without Sheila's say-so.
- Writing: no em dashes; never say leads "clicked on the site"; short, about the setters' calls, not the machinery.
- If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop.

## Files

| File | What it does |
| --- | --- |
| `SCRIPT-objections.md` | Snapshot of the script's objection sections (Oct 25). The live Google Doc `1qjF3Q-VngJ2LwSl_zHItRZTPHHR6uQu2X55M1rTWqk4` wins |
| `RUBRIC.md` | Which calls count, objection tags, Hit / Partial / Miss rules, roll-up |
| `kit/oc_collect.py` | **Workbench.** `prepare(D)`: the three setters' calls on D, recordings of 60+ sec, lead names and outcomes, a signed audio link per call (1 hour), all in one shared JSON (`calls_link`). `model_links()`: signed links to the faster-whisper `small.en` files. Both run in a kernel thread: call again until the answer isn't `'working'` |
| `kit/oc_local.py` | **Claude container.** `model LINKS.json DIR` fetches the model; `run CALLS_LINK WORKDIR MODEL_DIR` downloads every recording, transcribes them in parallel and writes `WORKDIR/bundle.json` |
| `kit/oc_tx.py` | Transcribes one recording (PyAV decode, 2-minute chunks, VAD, a vocabulary prompt for our words) |
| `kit/oc_publish.py` | **Claude container.** `build BUNDLE GRADES EXISTING_DIR OUT_DIR`: checks the grades file against the bundle, turns it into rows, merges them into the dashboards' current files (replacing that day) and writes `headline.txt` |
| `PROMPT.md` | The scheduled task's prompt |

**Why it's split this way (Oct 25).** The workbench (1 CPU, about 1 GB RAM, of which ~400 MB is free) can't transcribe long calls: the first full batch lost 39 of 42 calls to the out-of-memory killer and the workbench crashed twice. The Claude container has 4 CPUs and 15 GB but can't reach Close, huggingface.co or Composio's short links. It *can* fetch the direct storage links (`*.r2.cloudflarestorage.com`) that the workbench hands over, so the workbench collects and signs, and the container transcribes. Friday Oct 23 (42 calls, 176 min of audio) took 16 minutes here with `small.en` (2 calls at a time, 2 threads each), all 42 transcribed.

Workbench notes:
- Cells must finish in under 60 seconds (the MCP client gives up at 60, before the workbench's own 180). That's why `prepare` and `model_links` run in a background thread. Exec `oc_collect.py` once per workbench; re-exec'ing resets the job table.
- A fresh workbench has no model: `model_links()` starts a background download (about a minute) and answers `'downloading'`; call again.
- Read a cell's result from its last expression, not `print`: printed output sometimes comes back empty.
- The MCP endpoint sometimes answers 403 or times out; retry. Cells containing `sleep` or raw environment-variable names drew a 403 more than once.
- Signed links expire after 1 hour: run `oc_local.py run` right after `prepare(D)`; it downloads all audio first.
- In the container: `pip install faster-whisper` (PyPI is reachable). faster-whisper's own decoder fails with the installed `av`, which is why `oc_tx.py` decodes with PyAV itself.

## Daily run (weekdays, 6:37am ET, done well before Bali's 8:45 scorecard uses the workbench)

1. Days to cover: the previous day in ET. On Monday cover Friday, Saturday and Sunday (setters do dial on weekends). Run each day below in turn, oldest first.
2. Re-read the live script doc (Google Drive `read_file_content`, id above). If the objection sections differ from `SCRIPT-objections.md`, grade against the live doc and add one line to Sheila: "The script changed since the Oct 25 snapshot: <what>."
3. Workbench (load COMPOSIO_REMOTE_WORKBENCH with ToolSearch): write `kit/oc_collect.py` from this repo to `/mnt/files/oc_collect.py`, check its md5 matches the repo copy, and `exec` it once. Then call `model_links()` and `prepare(dt.date(Y,M,D))` (`import datetime as dt`), one quick cell at a time, until neither answers `'working'` or `'downloading'`. `prepare` returns calls per setter, how many 60+ second recordings, minutes of audio and `calls_link`.
4. Claude container: `pip install -q faster-whisper`, then confirm `python3 -c "import faster_whisper"` works before anything else (two runs started transcribing before the install finished and had to redo the pass). Save the `model_links()` dict as `links.json`, then `python3 objections/kit/oc_local.py model links.json <scratch>/model-small.en` and `python3 objections/kit/oc_local.py run '<calls_link>' <scratch>/oc-D <scratch>/model-small.en` (run it in the background and wait for `bundle.json`). Read `bundle.json`: one row per call with the transcript.
5. Grade every call by `RUBRIC.md` yourself in this session (don't hand it to the workbench `invoke_llm`), and write the result as `<scratch>/grades-D.json` in the format under "Grades file". Every call in the bundle gets an entry, voicemails included.
6. Publish to both dashboards as in "Publishing" below: download their current files, `python3 objections/kit/oc_publish.py build <scratch>/oc-D/bundle.json <scratch>/grades-D.json <scratch>/pub/existing <scratch>/pub/out`, upload, point the datasets at the new files. If `build` stops with a "grades file problem", fix the grades file and run it again. On Monday, run days oldest first; each day's `out` is the next day's `existing`, and you upload once at the end.
7. Tell Sheila with one PushNotification (status proactive) and nothing else: "Setter objection check, <Weekday Mon DD>:" then the lines of `headline.txt`, then the two links (scorecard first, then library). On Monday, one line block per day. Add "The script changed since the Oct 25 snapshot: <what>." when step 2 found a change.
8. A day where none of the three made a call of 60+ seconds still gets published (dials only, so the cards say "no real conversations").
9. If transcription failed for some calls, give them type `unclear` with no objections, say how many in the message, and grade the rest; never guess a call's content from Close fields.
10. If publishing fails, send the headline lines and say the pages weren't updated and why; don't retry more than once.

## Grades file

One JSON object per day. `oc_publish.py` takes lead, time, length, setter and the Close link from the bundle; the grades file only says what you judged.

```json
{
  "day": "2026-10-26",
  "calls": [
    {"call_id": "acti_...", "type": "conversation", "booked_live": true,
     "objections": [
       {"objection": "Price", "lead_words": "How much is it?",
        "grade": "Miss", "decided_by": "Quoted \"$20,000 one time\" on its own; no range, no booking ask.",
        "instead": "The script's line for this objection, fitted to the call, ending in a live booking ask."}
     ]},
    {"call_id": "acti_...", "type": "voicemail", "booked_live": false, "objections": []}
  ],
  "coaching": [
    {"setter": "Bali", "focus": "One-line main miss", "lead_said": "Quote (Lead, HH:MM)",
     "setter_said": "Quote", "script_says": "The script line", "best_moment": "One sentence with a quote, or empty"}
  ],
  "flags": [{"setter": "Jordan Kempster", "flag": "Short name", "detail": "What was said, with the quote and lead"}]
}
```

- `type`: `conversation`, `voicemail`, `screener`, `logistics`, `unclear` or `cut off` (recording ends before the call does). Only conversations carry objections and `booked_live`.
- `booked_live`: true when a closer call was booked on this call (the setter books it while the lead is on the line).
- `objection` (RUBRIC tag in brackets): `Price` (price), `Send me info` (send_info), `Not right now` (not_now), `Is this legit` (legit), `I can do this myself` (diy), `Quick answer` (quick:*), `Other` (other). A conversation with no objection has `"objections": []`.
- `grade`: `Hit`, `Partial` or `Miss`. `decided_by`: the setter's words or action that decided it. `instead`: for a Partial or Miss, what the setter should have said per the script, fitted to the call (empty for a Hit).
- `coaching`: one entry per setter who had conversations; `focus` empty if nothing to coach. `flags`: off-script claims and leads handled against the qualifying rules (RUBRIC section 4).
- Setter names exactly: `Bali`, `Jordan Kempster`, `Jose Rodriguez`. Quotes are the transcript's words. No em dashes (the script refuses them).

## Publishing

The scorecard holds five files (datasets `calls`, `objections`, `coaching`, `flags`, `days`); the library holds one (`objections`, the same file). Use the Artifact tool and the ArtifactData tool (load it with ToolSearch).

1. `Artifact` `action: "read"` on each dashboard's link once (a publish to an artifact this session hasn't read is refused).
2. For each of the scorecard's five datasets: `ArtifactData` `get`, collection `datasets`, doc_id `<dataset>`. Note its `version` and `source.url` (`/_blob/<id>`). Download it with `Artifact` `action: "read"`, `path: "<id>"` (one call per file: `paths` does not fetch uploaded files), `out_dir: "<scratch>/pub/dl"`; it saves as `<id>.json`. Copy that to `<scratch>/pub/existing/oc-<dataset>.json`. If a download fails, stop: merging onto an empty file would drop the history.
3. Run `oc_publish.py build` (step 6 above).
4. Upload each `<scratch>/pub/out/oc-<dataset>.json` to the scorecard with `Artifact` `asset: true`, `url`, `file_path` (one call per file), and `oc-objections.json` once more to the library. Each reply gives a new `/_blob/<id>`.
5. `ArtifactData` `batch` on each dashboard: one `update` per dataset, `if_version` = the version from step 2 (for the library, `get` its `datasets/objections` first), data `{"source": {"kind": "file", "url": "/_blob/<new id>", "name": "oc-<dataset>.json"}, "updated": {"at": "<ISO time now>", "by": "Setter objection check (Claude)"}}`.
6. Delete the replaced files: `Artifact` `action: "delete"`, `url`, `path: "<old id>"`, only after step 5 succeeded.
7. Don't touch `files/index.html` or `dash/meta`, and don't read the pages' check or runs documents: the page code doesn't change.

The files grow by roughly 25 KB a working day for objections; the dashboards take up to 8 MB per file, so about a year before it needs splitting. Say so to Sheila when `oc-objections.json` passes 6 MB.

## Known limits

- Transcripts have no speaker labels. Speaker is inferred from content; lines that can't be attributed are marked unclear and not graded against the setter.
- Whisper (`small.en`) mishears names and brand words. The grade is about meaning, not exact wording.
- Calls under 60 seconds are not reviewed, so quick brush-offs ("send me something", hang-ups) on short calls are not graded.
- Grades are Claude's reading of the transcript and can vary a little run to run on borderline calls (the Oct 23 pilot and the Oct 26 routine rerun of the same day gave Bali 18% and 27%). The library's "What decided it" column shows the reasoning for each grade, so a disputed call can be checked.
