# Setter objection check (daily): runbook

Owner: Sheila Xu (sheila@smbdealhunter.xyz). Set up Oct 25, 2026. Setters: Bali (Jabali Dumas), Jordan Kempster, Jose Rodriguez.

A daily report for Sheila only: how well each setter handled objections on their real conversations the previous dialing day, graded against the objection section of the "Setter Inbound Call Script_Oct 2026" (the Welcome Series Outbound SOP, Step 4, points there). It is its own report, separate from Bali's scorecard and from the "Setter handoff check" task (Sheila, Oct 25).

## Rules

- Read-only: never write to Close, never post to Slack, never message a setter. Sheila shares the report herself.
- Close data and recordings come through the Composio remote workbench (`proxy_execute`, `close` toolkit). Close has no transcripts and won't turn them on (Sheila, Oct 25): we transcribe ourselves with faster-whisper in the workbench.
- Only recordings of 60+ seconds are transcribed (Sheila, Oct 25). Voicemails, screeners and logistics calls are skipped at grading.
- Grading follows `RUBRIC.md`. Don't change the rubric, the 60-second floor or the report layout without Sheila's say-so.
- Writing: no em dashes; never say leads "clicked on the site"; short, about the setters' calls, not the machinery.
- If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop.

## Files

| File | What it does |
| --- | --- |
| `SCRIPT-objections.md` | Snapshot of the script's objection sections (Oct 25). The live Google Doc `1qjF3Q-VngJ2LwSl_zHItRZTPHHR6uQu2X55M1rTWqk4` wins |
| `RUBRIC.md` | Which calls count, objection tags, Hit / Partial / Miss rules, roll-up |
| `kit/oc_collect.py` | Workbench: `start_day(D)` pulls the calls, saves `calls.json`, starts the background batch; `batch_status(D)`; `bundle(D)` |
| `kit/oc_batch.py` | Workbench background driver: downloads each recording (raw proxy, `binary_data.url`) and runs `oc_tx.py` once per recording; resumable |
| `kit/oc_tx.py` | faster-whisper `base.en` int8, 1 thread, VAD on, decoded with PyAV to 16 kHz mono |
| `PROMPT.md` | The scheduled task's prompt |

Workbench notes (from Oct 6 and Oct 25 tests): 1 CPU, about 1 GB RAM. Install faster-whisper in the background (`pip install -q faster-whisper` via `subprocess.Popen`), never in the foreground. Model cache in `/home/user/whisper`. Speed is about 0.15x real time with VAD (a 68-second call took 10 seconds). While the batch runs the workbench is slow to answer: keep polling cells tiny (`len(os.listdir(...))`), and expect an occasional timeout or 403 from the MCP endpoint; just retry. A cell whose text contains `sleep`, `ps aux` or raw environment-variable names has drawn a 403 more than once, so poll without them.

## Daily run (weekdays, 6:37am ET, before Bali's 8:45 scorecard so the two never share the workbench CPU)

1. Days to cover: the previous day in ET. On Monday cover Friday, Saturday and Sunday (setters do dial on weekends). Run each day below in turn, oldest first.
2. Re-read the live script doc (Google Drive `read_file_content`, id above). If the objection sections differ from `SCRIPT-objections.md`, grade against the live doc and add one line to Sheila: "The script changed since the Oct 25 snapshot: <what>."
3. Workbench: write `kit/oc_collect.py`, `kit/oc_batch.py`, `kit/oc_tx.py` from this repo to `/mnt/files/` (overwrite; they're small). Make sure `faster_whisper` imports (`importlib.util.find_spec`); if not, start the background install and wait for it. Then `exec(open('/mnt/files/oc_collect.py').read())`, `import datetime as dt`, and `start_day(dt.date(Y,M,D))`. It returns calls per setter, how many 60+ second recordings, and minutes of audio.
4. Poll `batch_status(D)` every few minutes (each poll its own short cell) until `finished`. Then `bundle(D)` and read `/mnt/files/objections/D/bundle.json` back in parts (print slices of a few calls at a time; a full day is about 40 calls).
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
