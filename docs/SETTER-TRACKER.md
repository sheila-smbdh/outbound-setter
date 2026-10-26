# Setter Follow-up Tracker (runbook)

Owner: Sheila Xu. Built Oct 25 to 26, 2026, at the setters' request: Close gives Bali, Jose and Jordan no good way to see everyone they have called and what each lead needs next.

**The sheet:** "Setter Follow-up Tracker", https://docs.google.com/spreadsheets/d/1R9G94XcDYBViugBPW0OEMBkueU1hHanedyyxaBn_lSU/edit (Sheila's Drive; she shares it with the setters). One tab per setter (Bali, Jose, Jordan) plus "How it works". Nobody types in it: every refresh rewrites each tab from Close. To change a lead's next step, the setter updates the lead in Close.

**Refresh:** once a day (Sheila, Oct 26), routine "Setter follow-up tracker", `CRON_TZ=America/New_York 41 8 * * *`, before any setter's shift starts. Prompt: `prompts/setter-tracker-routine.md`.

## Decisions (Sheila, Oct 26, 2026)

- Google Sheet, not a Claude page. Daily refresh. Overdue leads get their own section under today's work.
- Bali's Abandoned Typeform leads follow the "Setter Abandoned Typeform Outbound SOP" (Google Doc `1pXszNKbcUglNTqoP74GBn2zarT9USTc-CbH9Ma3kva0`), the same cadence as `docs/ABANDONED-TYPEFORM.md`.
- The tracker only reads Close and only writes this sheet.

## Files

| File | What it does |
|---|---|
| `kit/setter_tracker.py` | Collector, next-step rules and sheet writer. Runs in the Composio workbench right after `bali_metrics.py`. `tracker_start()`, then `tracker_step()` until it returns "... done" |

The workbench cuts a call off at about 60 seconds and restarts when that happens, so the run is about 30 short steps. Each saves progress to `/mnt/files/tracker_state.pkl`, so a restart resumes where it stopped. Everything is prefixed `TRK_` / `_trk_` because the workbench is shared and `bali_show.py` also defines `SETTERS`. The tracker keeps its own Close pager, because `wb_runner.py` swaps `get_all` for a cache.

## Which leads

- **Welcome Series:** sign-ups in the "Welcome Series - Bali Test" workflow (`SEQ`) from the last 14 days whose Close field "Initial Contact User" is the setter (the same list rule as the scorecards, runbook "Three setters and the v5 cards").
- **Abandoned Typeform (Bali only):** every lead whose field "Incomplete Typeform User" is Bali. Its "Signed up" date is when it entered the "001- Incomplete Typeform Lead Distribution" workflow.
- Calls, texts and emails are the setter's own, from the last 15 days. Picked up, voicemail and no-voicemail-option use the scorecard's rules (`classify()`, `no_vm_option()` in `bali_metrics.py`).

## Sections, top to bottom

1. **New: not called yet.** Signed up yesterday or today, never called.
2. **Due today.** Follow-up calls due today, callbacks due today, handoff steps due today.
3. **Talked, no next step in Close.** Picked up, but no meeting and no open callback task.
4. **Overdue.** Missed follow-ups, missed callbacks, and sign-ups older than yesterday that were never called.
5. **Coming up.** Scheduled for a later day.
6. **Nothing left to do.** Closed out, closer call held, or every SOP try done.

## Next-step rules, in order

1. **Closed out:** lead status Do Not Contact, disqualified, not a fit, Won or Lost, or the last pickup's outcome is Disqualified, not a fit or Do not contact.
2. **Meeting ahead** (not canceled):
   - On the setter's own calendar: "Your own call with them".
   - With a closer (SOP 4A): booked today means the handoff email (checked against the "Discovery Call" email subject) plus setter notes by end of day. A call tomorrow means the day-before reminder today. A call today means the morning-of reminder if they haven't replied. Otherwise it goes under Coming up, with the reminder date.
3. **Talked and the closer call already happened:** done.
4. **Talked:** the earliest open Close task on the lead (not the Welcome Series workflow task) sets the date. Without one, the lead goes under "Talked, no next step".
5. **Never called:** New if signed up yesterday or today, else Overdue.
6. **No pickup, Welcome Series (SOP 4C):**
   - First called today: try 2 later today (dial only), plus any missing try 1 step (double dial within 2 minutes, voicemail unless the call never reached a mailbox, text).
   - First called yesterday: try 3 today.
   - Earlier with no later call: try 3 missed (Overdue).
   - Called again on a later day: 3 tries done.
7. **No pickup, Abandoned Typeform:**
   - Day 1 is the first call.
   - Day 3, 5 and 7 are 2, 4 and 6 business days later, each a call and, if no answer, double dial, voicemail and text.
   - Then a monthly call: 30 days after Day 7, then every 30 days, moved to the next business day if needed.
   - The next due call is the first one after the last call. Before today it is Overdue; today it is Due today.
   - Calls today with a missing double dial, voicemail or text also show as Due today.

## Known limits

- One refresh a day: try 2 and same-day callbacks show from the next morning only, and leads that sign up during the day appear the next morning. The setters still work new sign-ups from the Close smart views as they come in.
- A callback with no Close task can't be dated; it shows under "Talked, no next step".
- Lead lists depend on the two Close fields. A lead missing "Initial Contact User" is on no one's tab (runbook open item: 25 Oct 19 and 20 sign-ups have Jordan's call task but Jose as Initial Contact User).
- Old overdue lists are long (Oct 26: Bali 388, Jose 428, Jordan 360, mostly never called). They drop off after 14 days (Welcome Series) or once called.
