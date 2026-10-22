# Bali Abandoned Typeform card (runbook)

Owner: Sheila Xu. Test started Wed, Oct 21, 2026. Card layout: per-lead version approved by Sheila on Oct 22 (`mockups/abandoned-typeform-mockup.png`; first live render `mockups/abandoned-typeform-2026-10-21-live.png`). It replaced the Oct 21 tile layout (`mockups/abandoned-typeform/`). SOP: "Setter Abandoned Typeform Outbound SOP" (Google Doc `1pXszNKbcUglNTqoP74GBn2zarT9USTc-CbH9Ma3kva0`).

This is a third image, separate from the two Welcome Series cards. It goes to Sheila only, as a DM in Slack every weekday at 8am ET, titled "Bali Abandoned Type Form". It never goes to Bali or to a channel.

## Files

| File | What it does |
|---|---|
| `kit/bali_abandoned.py` | Close collector. Runs in the Composio workbench after `bali_metrics.py`, `bali_cover.py` and `bali_show.py`. `run_abandoned(D)` returns the metrics dict |
| `kit/abandoned_build.py` | Renderer. `python3 abandoned_build.py metrics.json out` writes the HTML, `scorecard-D-3-abandoned.png` and `abandoned-links-D.txt` (the lead names as Slack links) |
| `prompts/abandoned-typeform-routine.md` | The exact prompt of the daily routine |

## Daily run (weekdays 8am ET)

1. D = the previous weekday in America/New_York (Monday uses Friday).
2. Workbench (shared with other sessions: keep results in uniquely named variables and save them to a file in the same cell): the copies of `bali_metrics.py`, `bali_cover.py`, `bali_show.py` and `bali_abandoned.py` in `/mnt/files/` must match this repo by md5 (write the repo copy when one is missing or different). Exec them in that order, then run `run_abandoned(D)` in a thread (each workbench call is cut off at about 60 seconds, so start the thread, `join(40)`, and poll in later calls). Dump the dict as JSON.
3. Render: `CHROMIUM_PATH=<chromium> python3 kit/abandoned_build.py metrics.json out`. Look at the PNG once.
4. Slack: upload the PNG to Sheila's self-DM `D0BLE68V517` (`slack_get_file_upload_url`, POST the bytes, `slack_complete_file_upload` with `channel_id` D0BLE68V517 and title "Bali Abandoned Type Form"). The comment is one line: "Bali Abandoned Type Form: <Weekday, Mon D>: speed X%, follow-ups Y of Z on time, show rate W%, N set to a closer."
5. Right after the card, send the contents of `out/abandoned-links-D.txt` as one `slack_send_message` to the same DM, so the lead names can be clicked (the PNG can't hold links).
6. If Bali made no calls to this list on D and no follow-up was due, send one text line to the same DM instead of the card.

## Definitions

- **Bali's list:** leads enrolled in the Close workflow "001- Incomplete Typeform Lead Distribution" (`seq_0i6NE63SCuSdwb4E7kXQc3`, the #partial-submit bucket) whose lead field "Incomplete Typeform User" (`cf_qiVzsFQUYHM2vmDeUg0mbfIrWgvU3ZJmhujqNtWiAhJ`) is Bali. Enrollments from Oct 1 on are checked, so older bucket leads assigned to him count too. The Smart View "Bali - Incomplete Typeform List" uses the same field.
- **Every number counts only this list.** Call rules are the Welcome Series ones (runbook "Definitions"): pickup, real conversation, voicemail, text, double dial, closer call, show rate, handoff steps.
- **Work hours (Sheila, Oct 22):** Bali gave his active hours as 7am to 5pm PT; Sheila asked for the 8 hours inside that he actually dials. `AB_HOURS` in `bali_abandoned.py` = 11am to 7pm ET (8am to 4pm PT), provisional: picked from his Oct 16 and Oct 21 dials (the best 8-hour block inside 10am to 8pm ET). Recheck against more days. The Welcome Series window (`WORK` in `bali_cover.py`, 9am to 9pm ET) is not changed.
- **Speed to lead:** leads that entered the bucket on D during the work hours (the #partial-submit ping), first Bali call within 15 minutes. Never called that day = miss.
- **Voicemail, text, double dial:** every lead on the list he dialed on D and didn't reach (the SOP asks for double dial, voicemail and text on every no-answer day, not just Day 1). Do Not Contact leads are left out; voicemail counts only people who gave him a chance to leave one; text leaves out blocked or invalid numbers; double dial counts no-answer calls redialed within 2 minutes.
- **Pickup and connect rate:** out of people on the list he dialed on D.
- **Set to a closer:** closer calls booked on D off his pickups on this list, split into Day 1 (booked on his first-call day) and follow-up days. **Sets so far:** unique leads set to a closer since Oct 21. **Closes so far:** Won deals on those leads, since Oct 21.
- **Show rate:** `run_show` from `bali_show.py`, limited to sets from this list: last 7 days, plus all sets since Oct 21, with the four handoff steps.
- **Follow-up calls on time (Sheila, Oct 21: business days):** Day 1 = his first call to the lead on or after Oct 21. Day 3, 5 and 7 = 2, 4 and 6 business days later (Mon to Fri; no holidays). Then monthly: 30 days after Day 7, then every 30 days, moved to the next business day if it falls on a weekend. A lead stops owing follow-ups once he has talked to them, they have a meeting booked, or they are Do Not Contact. On time = called on the day it was due. The table lists every lead due on D.
- **Targets (Sheila, Oct 21):** speed 60%, voicemail 85%, text 85%, double dial 85%, pickup 25%, connect 10%, show rate 90%, follow-ups on time 90%. Green at target, yellow at 75% of target or more, red below. "Set to a closer" has no target.
- **Dials stay separate from Welcome Series (Sheila, Oct 21).** Pending: the Welcome Series card still counts every Bali dial toward 200, because the live Welcome Series run reads the claude.ai Project copy of the kit. Excluding this list there is a change to `bali_metrics.py` to make at cutover, with Sheila's OK on the exact rule.

## The card (Sheila, Oct 22, 2026)

Talks to Bali as "you". Top to bottom:

1. **Header:** the day's leads (every lead that entered the bucket on D, any hour), how many he called, picked up and set, and sets and closes since Oct 21.
2. **Four tiles:** speed to lead (bucket entries during his work hours, below), pickup rate and connect rate (out of the day's leads he called), set to a closer (from the day's leads; the tile adds the day's total when an older lead was also set).
3. **Two blocks: during your hours and outside your hours** (Sheila, Oct 22). Each has a bar splitting its leads into four groups, then the tables below.
4. **One table per group,** every lead name linked to its Close page, with how fast he called (green at 15 min or less), what happened and the next step (red when something is overdue):
   - **Real conversations** (same rule as Welcome Series): the result (set to which closer and when, booked on his calendar, call back later, disqualified) and, for closer sets, the four handoff steps (done, missed, still ahead, or not owed). Next step: the first missed step, else the next one due, else the closer call. Call back later uses his open Close task date, or asks him to set one.
   - **Picked up, no real conversation:** what happened and his next Close task, or "Set a next step in Close".
   - **Didn't pick up:** four equal tiles above the table (double dialed, voicemail, texted, called in 15 min; the last one only in the in-hours block), then double dial, voicemail and text marks (a dash when the call never reached a mailbox or the number can't take a text). Next step: "Text now" when he missed the text, then the Day 3 call date (2 business days after Day 1).
   - **Not called yet:** when the lead entered, and "Day 1 call now".
   - A Do Not Contact lead's next step is "None, Do Not Contact".
5. **Follow-up calls due D:** earlier leads on their Day 3, 5, 7 or monthly call (rules below), shown only when any were due.
6. **Closer calls that happened D:** leads he set on earlier days whose closer call was on D, with the closer, whether they showed and the handoff steps; the 7-day show rate in the heading.

## Known limits

- The list depends on the "Incomplete Typeform User" field. A lead Bali calls from the bucket without the field set to him is not counted.
- Day 1 is his first call, not the bucket date, so a lead he never calls never enters the follow-up table (it shows as a speed-to-lead miss on its bucket day instead).
