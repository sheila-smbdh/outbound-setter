# Inbound setter scorecards: data sources (Sheila, Nov 20, 2026)

Approved layouts: `mockups/inbound-scorecards/` (v7). Built Nov 20, 2026. Delivery: the routine in `prompts/inbound-scorecards-routine.md` (weekdays 9am ET; inbound cards to #setter-sync `C095GLLCU2U`, Jose's outbound card to `C0C9VANP6QN`), created paused; Messi's two reports were fixed Nov 23, 2026, and Sheila turns the routine on.

## Files

| File | What it does |
|---|---|
| `kit/inbound.py` | Inbound sets, handoff steps, the week's verdicts and the table rows (`run_inbound`). Runs after `bali_metrics.py`, `bali_cover.py`, `bali_show.py` |
| `kit/run_inbound.py` | `python3 run_inbound.py <D> jose jordan dave --flags ../flags --out <dir>` writes `inbound-<key>.json` (GET only, same Close access as `run_direct.py`) |
| `kit/inbound_build.py`, `kit/inbound.css` | Render `inbound-<key>.json` to `inbound-<key>-<D>.png` |
| `flags/<D>.json` | Messi's price and booking results for a day, written by the routine from Slack (format in `kit/inbound.py`) |
| `kit/inbound_draw.py` | Merge the run into the tracker tabs: `python3 inbound_draw.py <days.json> <weeks.json> <inbound-*.json> --out <dir>` writes the Sheets `values:batchUpdate` body |
| `kit/inbound_supabase.py` | Supabase rows for a run: one JSON file per table plus the curl upsert for each |
| `kit/inbound_corrections.json` | One-off fixes Sheila or Jay approved in a card thread |
| `supabase/inbound_scorecards.sql` | The Supabase tables (run once) |
| `jose_it` in `SETTERS` (`kit/bali_show.py`) | Jose's Incomplete Typeform outbound card: `python3 run_direct.py <D> jose_it`, then `build.py` (labels in `CARDS`, `kit/build.py`) |

## Cards

| Card | Who | KPIs | Draw |
|---|---|---|---|
| Inbound | Jose Rodriguez, Jordan Kempster | 1 handoff steps 100%, 2 no price, 3 no direct-to-closer booking | Yes, weekly; a compliant day needs all 3 |
| Inbound | Dave (David Martin, Close user `user_sByZkVjk2If3ioL4CC26O5JmTWuzzKzDEjr9fzZHJ26`) | Same 3 KPIs | No draw; no draw wording, no outbound tile |
| Incomplete Typeform outbound | Jose | Same tiles as the Welcome Series v5 card | Tracked only, no effect on KPIs or the draw |

No Incomplete Typeform dials on the day (Sheila, Nov 25, 2026): no card; the routine posts one line to C0C9VANP6QN instead, "@Jose @Jay @Sheila No Incomplete Typeform outbound dials were made on Tuesday, Nov 24.", so Jay and Sheila see the outbound activity every day.

## Top tiles (inbound cards)

- **Inbound sets to a closer today / this week:** inbound sets only. Jose's Incomplete Typeform sets stay on his outbound card.
- **Closes / outbound sets since Oct 20** (Jose and Jordan only): every outbound set since they started outbound on Oct 20, Welcome Series and, for Jose, Incomplete Typeform (since Nov 11). A is the closes from those sets.

## Booked, scheduled and live calls (Sheila, Nov 23, 2026)

Three blue tiles under the sets tiles on every inbound card (Jose, Jordan, Dave). Tracked only: no target, no green or red. Counted for the card's day, one per lead, from every call on the setter's own calendar (intro calls and the setter's follow-ups). `call_counts()` in `kit/inbound.py`.

- **Booked:** every lead with a call on the setter's calendar starting that day, canceled or not. A rebooked call counts again on its new day.
- **Scheduled:** booked, minus:
  - calls canceled or asked to be rescheduled **before the call day**;
  - reschedules asked **on the call day before the start time**.
  - A cancel on the call day, or a reschedule asked after the start time, stays in: it is a no-show.
  - A reschedule is: the call canceled with a new call booked for the same lead within 30 minutes; a new call with the setter booked before the old one's start; or a text or email from the lead asking to move it ("reschedule", "push to Monday", "another time", ...). A cancel is: canceled with nothing rebooked, or a message saying they can't make it or want to cancel. Calendly's own emails and quoted earlier messages are skipped. Close keeps no cancel time, so a canceled call's last update stands for it.
- **Live:** the lead joined the Zoom. A live call always counts as scheduled.
- Checked Nov 20, 2026: Dave 8 booked, 6 scheduled (Paul Caruana texted "I will have to reschedule" at 1pm for 4pm; Scott Nowicki emailed "Going to have to push to Monday" and rebooked before 2:30pm), 3 live. Jose 10, 10, 7 (Mir Karim canceled at 3:01pm for 4pm, nothing rebooked: a no-show).
- Message reading is a word match, so an unusual phrasing can be missed; the card JSON (`calls.rows`) lists each lead and why it was removed.

## What counts as an inbound set

Same rules as the outbound card's sets (`_bookings` in `kit/bali_metrics.py`), plus confirmation that the setter actually set the lead (Sheila: check, double-check, triple-check):

1. The lead booked the setter's 15-minute intro call. It shows in Close as a meeting on the setter's calendar (Calendly booking, Zoom recording attached).
2. The setter talked to the lead on that call (Zoom joined, same check as `zoom_talks()`).
3. The lead then has a closer meeting booked after that call.
4. The setter's closer note and handoff email back it up.

If 1 to 3 hold but the note or the email is missing, it still counts as the setter's set, and the missing step shows as a red miss (Sheila, Nov 20).

## KPI 1: handoff steps

Same as the outbound card (`lead_steps()` in `kit/bali_show.py`): handoff email to the closer and closer note in Close, day-before and day-of texts sent from Close, with the same rules (no day-before text when the call is the next day; no day-of text owed when the lead replied or accepted the invite; none for follow-up closer calls after the first show). Done by the end of the setter's workday. The handoff email counts when it uses the "Setter to Closer Handoff" template, has its subject line, or (Sheila, Nov 26, 2026) is one email from the setter to both the lead and the set's closer that introduces them, naming the closer and the call (`_intro_email()`; runbook, Handoff steps).

Only inbound sets count. Reminders still owed on old Welcome Series outbound sets do not go on the inbound card (Sheila, Nov 20).

## KPI 2: price (Messi, #ai-call-review-test `C0C3JB44155`)

- Nov 23, 2026 (Sheila): fixed. One top-level "Setter Program Price Check · <date>" post per day, the day after, with "no price dropped, all clear" or the alerts. It runs at 5am ET (Sheila, Nov 23; the Nov 22 one posted at 11:05am only because of testing), before the 9am routine. No post for a day means price shows "not checked" for it.

- Messi's setter price job (`d054ebfd6f6c`) checks the previous day's calls for Dave, Jose and Jordan: Zoom recordings for inbound, Close call transcripts for Jose's outbound.
- It flags only a concrete dollar amount for the program (Messi learned rule #67). Sheila's approved wording for the price question is not a miss (#66).
- Each alert has the setter, lead, time and exact quote, posted as a new top-level message in the channel.
- On a clean day Messi posts a one-line all-clear (Sheila asked Messi, Nov 20). The card marks price green only when it sees that line. With no alert and no all-clear, it shows "not checked", not green.
- Messi's "Setter Call Script Compliance Report" (red/green per setter) is not used on the card (Sheila, Nov 20).

## KPI 3: direct-to-closer bookings (Messi, #sales-reports `C0C5CGGGE1M`)

- Nov 23, 2026 (Sheila): fixed. A dated parent post each day; in its thread nothing (or "clear") means all clear, an error reply means Sheila must fix the bot, and "New booking alert" replies list "Setter → Closer · call time" with the lead's Close link. Alerts are matched to sets by Close lead id (`_match`, `_booking_by_day` in `kit/inbound.py`). An alert can land days after the booking (Nov 21's thread held Jose's Nov 19 bookings of Shrikar Archak and Drew Davis on Kevin Manuel's own link), so an alert about one of the setter's sets counts on the day the set was made, and every run refreshes the whole week.
- Every direct booking shows the lead's name, the closer and the call time, on the card (under the table) and in the tracker's Why column (Sheila, Nov 23, 2026). The kit looks the name up in Close when Messi's alert only has the Close link. A flagged booking that isn't one of the setter's inbound sets says why in brackets: "not a set: meeting canceled", "not an inbound set: Incomplete Typeform lead, counted on the outbound card" or "not an inbound set".

- Messi posts a dated "DIRECT-TO-CLOSER BOOKING ALERTS" thread each day and adds a reply for each direct booking it finds. It runs every 15 minutes.
- Silence means clean (Sheila, Nov 20). Messi posts a one-liner in the thread when a run errors (Sheila asked Messi, Nov 20). A day with an error line shows "not checked" on the card, not green.

## The draw (Sheila, Nov 20, 2026)

- **No draw wording on the scorecards (Sheila, Nov 23, 2026):** whether Jose and Jordan get a draw from December isn't decided, so no card mentions a draw: the inbound cards' heading is "Every set, every step: all of it, every day" and Jose's Incomplete Typeform card says "This card does not count toward your KPIs. Your inbound card has your KPIs." The tracker is unchanged.

- Jose and Jordan are eligible for a week's draw when **every weekday, Monday to Friday, is compliant** on all 3 KPIs. Draw weeks start **Mon Nov 23, 2026**. Dave has no draw.
- A weekday with no intro calls, no inbound sets and no handoff steps due is not compliant. Sheila or Jay override days off.
- A day Messi's price or booking check didn't come in for is "Not checked" (not compliant, not missed) until Messi reports it or Sheila or Jay override it. Each run refreshes every day of the week so far, so a late Messi report fixes the day on the next run.

## Draw tracker (Sheila, Nov 20, 2026)

Two tabs in the Google Sheet "Setter Draw Tracker" (`1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE`), written by the inbound scorecards routine each run (`kit/inbound_draw.py`; standing approval, Sheila, Nov 20):

- **Inbound Days:** one row per setter per weekday: intro calls, inbound sets, handoff steps due and done, the three KPIs (Met, Missed, None due, Not checked), the day verdict and why. **P "Override (Sheila/Jay)"** (Compliant or Not compliant) and **Q "Override note"** are Sheila's and Jay's; the routine never writes them. **R "Counts as"** is the override if set, else the verdict.
- **Inbound Weeks:** one row per setter per week: Mon to Fri ("Counts as" from Inbound Days), compliant days of 5, the auto result (Eligible at 5 of 5, Not eligible once any day is not compliant, else In progress). **J "Override (Sheila/Jay)"** (Eligible or Not eligible) and **K "Override note"** are theirs; **L "Eligible for the draw"** is the override if set, else the auto result.
- Both tabs are protected: only Sheila and Jay can edit them. Everyone the sheet is shared with can still view them (10 editors and the smbdealhunter.xyz domain as of Nov 20).
- The routine writes Inbound Days A:O and R, and Inbound Weeks A:I and L, nothing else. Rows are upserted by (date, setter) and (week, setter), so overrides stay on their rows.
- The card's week dots come from the run's own verdicts, not the overrides.
- **Booked, scheduled and live calls** (Sheila, Nov 23, 2026): Inbound Days S:U per day (the routine writes them), Inbound Weeks M:O the week's totals (SUMIFS formulas). Jose and Jordan only; Dave's are in Supabase.

## Supabase (Sheila, Nov 23, 2026)

Every run records everything in setter-data (`suoblmuvrmyfmuvlhqce`), tables in `supabase/inbound_scorecards.sql` (run once in the SQL editor; Claude's Supabase access can't create tables). `kit/inbound_supabase.py` writes one JSON file per table and prints the curl upsert for each; the routine sends each with one inline curl (standing approval, Sheila, Nov 23, 2026).

| Table | One row per |
|---|---|
| `inbound_sc_days` | setter (Jose, Jordan, Dave) per weekday: intro calls, sets, booked/scheduled/live, the three KPIs, verdict and why, Messi's hits, outbound totals |
| `inbound_sc_sets` | inbound set: lead, closer, set and call times, each handoff step, price and booking |
| `inbound_sc_calls` | lead per day on the setter's calendar: scheduled, live, why removed |
| `outbound_sc_days` | Jose's Incomplete Typeform card per day (key numbers and the full metrics) |
| `inbound_sc_runs` | run: card day, status, summary |
| `inbound_sc_feedback` | setter's claim in a card thread, Sheila's or Jay's decision, what changed |

Rows are upserted on their keys, so a rerun or a correction replaces them in place.

## Feedback in the card threads (Sheila, Nov 23, 2026)

- Each run reads the threads on the cards posted in the last 14 days (#setter-sync and the outbound channel). A setter's reply saying a number is wrong, and why, is recorded in `inbound_sc_feedback` as pending.
- It changes nothing unless **Sheila or Jay** reply in that thread agreeing ("your response makes sense"). A setter's word alone never changes a number. A disagreement from Sheila or Jay marks it rejected.
- An approved claim is applied by the routine:
  - a one-off fix about specific leads goes in `kit/inbound_corrections.json` (format above `corrections()` in `kit/inbound.py`: a call's scheduled or live, a set excluded, a handoff step done or missed);
  - a change to how something is counted goes in "Approved corrections" below, with the code change in `kit/inbound*.py`.
  - The routine re-runs the affected days, checks the disputed number now matches what was agreed, commits to main, refreshes Supabase and the tracker for those days, and DMs Sheila a line per change. If it can't make the numbers match, it commits nothing and asks Sheila.
- The routine never replies in the card threads.

## Approved corrections

Rules added from approved feedback, newest last (date, setter, what changes, thread, who approved). None yet.
