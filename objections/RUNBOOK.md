# Setter objection check (daily): runbook

Owner: Sheila Xu (sheila@smbdealhunter.xyz). Set up Oct 25, 2026. Setters: Bali (Jabali Dumas), Jordan Kempster, Jose Rodriguez.

A daily report for Sheila only: how well each setter handled objections on their real conversations the previous dialing day, graded against the objection section of the "Setter Inbound Call Script_Oct 2026" (the Welcome Series Outbound SOP, Step 4, points there). It is its own report, separate from Bali's scorecard and from the "Setter handoff check" task (Sheila, Oct 25).

## Rules

- Read-only: never write to Close, never post to Slack, never message a setter. Sheila shares the report herself.
- Close data and recordings come through the Composio remote workbench (`proxy_execute`, `close` toolkit). Close has no transcripts and won't turn them on (Sheila, Oct 25): we transcribe the recordings ourselves with faster-whisper (the workbench collects, the Claude container transcribes; see Files).
- Only recordings of 60+ seconds are transcribed (Sheila, Oct 25). Voicemails, screeners and logistics calls are skipped at grading.
- Grading follows `RUBRIC.md`. Don't change the rubric, the 60-second floor or the report layout without Sheila's say-so.
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
| `PROMPT.md` | The scheduled task's prompt |

**Why it's split this way (Oct 25).** The workbench (1 CPU, about 1 GB RAM, of which ~400 MB is free) can't transcribe long calls: the first full batch lost 39 of 42 calls to the out-of-memory killer and the workbench crashed twice. The Claude container has 4 CPUs and 15 GB but can't reach Close, huggingface.co or Composio's short links. It *can* fetch the direct storage links (`*.r2.cloudflarestorage.com`) that the workbench hands over, so the workbench collects and signs, and the container transcribes. Friday Oct 23 (42 calls, 176 min of audio) took about <PILOT_MIN> minutes here with `small.en`.

Workbench notes:
- Cells must finish in under 60 seconds (the MCP client gives up at 60, before the workbench's own 180). That's why `prepare` and `model_links` run in a background thread. Exec `oc_collect.py` once per workbench; re-exec'ing resets the job table.
- A fresh workbench has no model: `model_links()` starts a background download (about a minute) and answers `'downloading'`; call again.
- The MCP endpoint sometimes answers 403 or times out; retry. Cells containing `sleep` or raw environment-variable names drew a 403 more than once.
- Signed links expire after 1 hour: run `oc_local.py run` right after `prepare(D)`; it downloads all audio first.
- In the container: `pip install faster-whisper` (PyPI is reachable). faster-whisper's own decoder fails with the installed `av`, which is why `oc_tx.py` decodes with PyAV itself.

## Daily run (weekdays, 6:37am ET, done well before Bali's 8:45 scorecard uses the workbench)

1. Days to cover: the previous day in ET. On Monday cover Friday, Saturday and Sunday (setters do dial on weekends). Run each day below in turn, oldest first.
2. Re-read the live script doc (Google Drive `read_file_content`, id above). If the objection sections differ from `SCRIPT-objections.md`, grade against the live doc and add one line to Sheila: "The script changed since the Oct 25 snapshot: <what>."
3. Workbench (load COMPOSIO_REMOTE_WORKBENCH with ToolSearch): write `kit/oc_collect.py` from this repo to `/mnt/files/oc_collect.py`, check its md5 matches the repo copy, and `exec` it once. Then call `model_links()` and `prepare(dt.date(Y,M,D))` (`import datetime as dt`), one quick cell at a time, until neither answers `'working'` or `'downloading'`. `prepare` returns calls per setter, how many 60+ second recordings, minutes of audio and `calls_link`.
4. Claude container: `pip install -q faster-whisper`. Save the `model_links()` dict as `links.json`, then `python3 objections/kit/oc_local.py model links.json <scratch>/model-small.en` and `python3 objections/kit/oc_local.py run '<calls_link>' <scratch>/oc-D <scratch>/model-small.en` (run it in the background and wait for `bundle.json`). Read `bundle.json`: one row per call with the transcript.
5. Grade every call by `RUBRIC.md`: call type, objections with the lead's quote, Hit / Partial / Miss per objection with the setter's quote, booked live, flags. Do the grading yourself in this session; don't hand it to the workbench `invoke_llm`.
6. Write the report (layout below) to `objection-check-D.md` and send it with SendUserFile (status proactive, display render), then one short message with the headline line per setter.
7. If a setter made no calls on D, say "no calls" for them. If none of the three made any calls, send one line and stop.
8. If transcription failed for some calls, list how many and grade the rest; never guess a call's content from Close fields.

## Report layout (Sheila only)

```
# Objection check, <Weekday Mon DD>

<Setter>: <N> conversations graded, <K> objections, <X>% handled per script.
(one line per setter; "no calls" or "no real conversations" when that's the case)

## <Setter>
Skipped: <a> voicemails, <b> screeners, <c> logistics/other.
Objections: price <n>, send info <n>, not now <n>, legit <n>, DIY <n>, other <n>.
Main miss: <one sentence>. "<setter quote>" (<lead>, <time ET>). Script: "<line they should have used>".
Best moment: <one sentence with quote>, or none.

| Lead | Time | Length | Objection (lead's words) | Grade | What decided it | Booked live |
(one row per objection; calls with no objection get one row "none")

Flags: <off-script claims, pitched under the bar>, or none.
```

Each lead name links to the call in Close (`close_url`). Keep the top section to the three lines; details go below.

## Known limits

- Transcripts have no speaker labels. Speaker is inferred from content; lines that can't be attributed are marked unclear and not graded against the setter.
- Whisper `base.en` mishears names and brand words. The grade is about meaning, not exact wording.
- Calls under 60 seconds are not reviewed, so quick brush-offs ("send me something", hang-ups) on short calls are not in the report.
