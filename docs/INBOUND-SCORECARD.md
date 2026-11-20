# Inbound setter scorecards: data sources (Sheila, Nov 20, 2026)

Approved layouts: `mockups/inbound-scorecards/` (v7). Not built yet. Delivery (where the cards post) is still to be decided with Sheila.

## Cards

| Card | Who | KPIs | Draw |
|---|---|---|---|
| Inbound | Jose Rodriguez, Jordan Kempster | 1 handoff steps 100%, 2 no price, 3 no direct-to-closer booking | Yes, weekly; a compliant day needs all 3 |
| Inbound | Dave (David Martin, Close user `user_sByZkVjk2If3ioL4CC26O5JmTWuzzKzDEjr9fzZHJ26`) | Same 3 KPIs | No draw; no draw wording, no outbound tile |
| Incomplete Typeform outbound | Jose | Same tiles as the Welcome Series v5 card | Tracked only, no effect on KPIs or the draw |

## Top tiles (inbound cards)

- **Inbound sets to a closer today / this week:** inbound sets only. Jose's Incomplete Typeform sets stay on his outbound card.
- **Closes / outbound sets since Oct 20** (Jose and Jordan only): every outbound set since they started outbound on Oct 20, Welcome Series and, for Jose, Incomplete Typeform (since Nov 11). A is the closes from those sets.

## What counts as an inbound set

Same rules as the outbound card's sets (`_bookings` in `kit/bali_metrics.py`), plus confirmation that the setter actually set the lead (Sheila: check, double-check, triple-check):

1. The lead booked the setter's 15-minute intro call. It shows in Close as a meeting on the setter's calendar (Calendly booking, Zoom recording attached).
2. The setter talked to the lead on that call (Zoom joined, same check as `zoom_talks()`).
3. The lead then has a closer meeting booked after that call.
4. The setter's closer note and handoff email back it up.

If 1 to 3 hold but the note or the email is missing, it still counts as the setter's set, and the missing step shows as a red miss (Sheila, Nov 20).

## KPI 1: handoff steps

Same as the outbound card (`lead_steps()` in `kit/bali_show.py`): handoff email to the closer and closer note in Close, day-before and day-of texts sent from Close, with the same rules (no day-before text when the call is the next day; no day-of text owed when the lead replied or accepted the invite; none for follow-up closer calls after the first show). Done by the end of the setter's workday.

Only inbound sets count. Reminders still owed on old Welcome Series outbound sets do not go on the inbound card (Sheila, Nov 20).

## KPI 2: price (Messi, #ai-call-review-test `C0C3JB44155`)

- Messi's setter price job (`d054ebfd6f6c`) checks the previous day's calls for Dave, Jose and Jordan at 5:00am ET: Zoom recordings for inbound, Close call transcripts for Jose's outbound.
- It flags only a concrete dollar amount for the program (Messi learned rule #67). Sheila's approved wording for the price question is not a miss (#66).
- Each alert has the setter, lead, time and exact quote, posted as a new top-level message in the channel.
- On a clean day Messi posts a one-line all-clear (Sheila asked Messi, Nov 20). The card marks price green only when it sees that line. With no alert and no all-clear, it shows "not checked", not green.
- Status Nov 20: the job is paused until Mitch approves posting to the channel (request #69).
- Messi's "Setter Call Script Compliance Report" (red/green per setter) is not used on the card (Sheila, Nov 20).

## KPI 3: direct-to-closer bookings (Messi, #sales-reports `C0C5CGGGE1M`)

- Messi posts a dated "DIRECT-TO-CLOSER BOOKING ALERTS" thread each day and adds a reply for each direct booking it finds. It runs every 15 minutes.
- Silence means clean (Sheila, Nov 20). Messi posts a one-liner in the thread when a run errors (Sheila asked Messi, Nov 20). A day with an error line shows "not checked" on the card, not green.
- Status Nov 18 to 20: runs were failing on a Calendly 403. Sheila asked Messi to resume.

## Still open

- Draw rule: how many compliant days a week earn the weekly draw.
- Delivery: where and when the cards post.
- The draw tracker for Jose and Jordan.
