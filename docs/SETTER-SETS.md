# Setter Sets report (runbook)

Owner: Sheila Xu. Built Oct 28, 2026, at Sheila's request: every setter's inbound and outbound sets by month and by week, from Close and from the self-reported tracker side by side, plus where the closers bucketed each lead that got set.

**The page:** "Setter Sets Aug to Oct 2026", https://claude.ai/artifact/AWv8pnwSTD3MixQGejukAy (a Claude dashboard, private to Sheila until she shares it). It reads three files attached to it; nothing on it refreshes by itself. To update it, follow "Refresh" below.

**Setters:** Bali (Jabali Dumas), Yobani Mendoza, Dave, Quinn Donelan, Jordan Kempster, Jose Rodriguez. Dave is **David Martin** in Close (`user_sByZ...`): he logs the forms and the intro meetings. The dave@ account (David Rendon) has no setter activity.

## Files

| File | What it is |
|---|---|
| `kit/setter_sets.py` | Collector and all counting rules. Runs in the Composio workbench on its own (needs none of the `bali_*.py` files). `ss_start(start, end)`, then `ss_step()` until it returns "... done", then `ss_result()` |
| `data/setter-sets/<end date>/monthly.csv` | Close and tracker sets per setter per month |
| `data/setter-sets/<end date>/weekly.csv` | The same per week (Monday to Sunday, cut at month ends so each month adds up) |
| `data/setter-sets/<end date>/buckets.csv` | Sets per setter, month, set type and closer bucket |
| `data/setter-sets/<end date>/leads.csv` | One row per set lead (from the 2nd run on; the Oct 28 snapshot has none, see below) |
| `dashboards/setter-sets/index.html` | The page's own source, as stored in the dashboard (`files/index.html`) |

The Oct 28 snapshot covers Aug 1 to Oct 28, 2026, Close as of about 3pm ET. It was built in an ad hoc session before `kit/setter_sets.py` existed; the script holds the same rules. Its lead-level list stayed in that session's workbench and was not saved, so the first scripted run is the first `leads.csv`.

## What counts (Sheila, Oct 28, 2026)

- **A set** is a lead a setter got onto a closer's calendar. Counted once per setter per lead, on the day it was booked (ET). Duplicate lead records in Close with the same name count once (Craig Fournier had 4 records).
- Close finds a set two ways, and either one counts:
  1. **Form:** the setter's "001) Pre-Discovery Call" form (`actitype_7eSCr8m78jZ35sh13poUg8`) with Pre-Strategy Call Outcome "03. Discovery Call Scheduled". The form's Activity Date (else its created time) is the set day.
  2. **Calendar:** a meeting on a closer's calendar created within 24 hours after the setter's call (any direction, 1+ second, not an `external` duplicate) or after an intro meeting on the setter's calendar. When two setters touched the lead, the latest touch wins.
  On Oct 28 about 85% of sets were found both ways. Form only: mostly Quinn, Dave, Jordan (their form, no closer meeting in the 24 hours). Calendar only: mostly Bali, Jose, Yobani (no form logged). Calendar-only sets can include a lead who booked the closer on their own after a setter's call.
- **Closers** (`SS_CLOSERS`): the 13 in `bali_metrics.py` plus Ezra Isla, Chris Cha and Kameron Bryant.
- **Inbound or outbound:** the form's "Type of Pre-Discovery Activity" ("Inbound / Scheduled Intro" or "Inbound/ Scheduled Discovery" = inbound, "Outbound" = outbound). With no form, or no type on it: inbound if the lead had an intro meeting on that setter's calendar in the 3 days before the closer meeting, otherwise outbound.
- **Left out:** Bali's Oct 5 sets for Matt Weiss and Dan Housley (Sheila, Oct 6: not his sets).
- **Tracker:** Google Sheet "Sales Tracker 2026 - Setting team" (`1TCO-KbUxwTs4qfLdmv2Dlt1BFipkdvfMRxW3Srwc_XI`), tab "Inputs", columns "Inbound sets" and "Outbound sets" per setter per day. Self-reported: shown next to Close, never mixed into the Close count. The page marks a month or week amber when the two differ by 3 or more.

## Closer buckets

The lead's current Sales pipeline opportunity (the newest one created from 3 days before the set on, else the newest). When it is Lost, or still at Discovery Call Scheduled, No Show/Cancel or Reschedule Request, the closer's latest "002) Discovery Call" Call Outcome after the set decides instead.

| Bucket | From |
|---|---|
| Won | WON, or outcome "10. Sale" |
| Short term: next 7 days / in month closing | Next 7 Days, In Month Closing |
| Short term: split pay or deposit | Split Pay/Deposit, or outcome "09. Deposit" (none so far; the page counts it with in month closing) |
| Long term: with intention | Long Term w/ Intention |
| Long term: no timeline, Long term: farming | Long Term No Timeline, Long Term Farm (Sheila, Oct 28: the page shows these two as one bucket) |
| Bad: bad fit | Lost with outcome Bad Fit, or outcome Bad Fit |
| Bad: offer not presented | Offer Not Presented |
| Lost, other reason | Lost with any other outcome |
| No show or canceled, Reschedule pending | No Show/Cancel, Reschedule Request (and the matching outcomes) |
| Call still ahead | a closer meeting on the lead still to come |
| Call passed, closer has not updated | none of the above: the call date passed and nothing was logged |

Closers rarely use Bad Fit (2 of 598 sets on Oct 28), so weak calls mostly sit in long term.

## Refresh

1. Pull the latest from the repo. In the Composio workbench, make `/mnt/files/setter_sets.py` match `kit/setter_sets.py` (md5), then:
   ```
   exec(open('/mnt/files/setter_sets.py').read()); import datetime as dt
   ss_start(dt.date(2026, 8, 1), dt.date(Y, M, D))   # D = the last full day
   ```
   then `ss_step()`, one per cell, until it returns "Setter sets ... done" (about 12 steps; unfinished pulls are retried on the next step), then `out = ss_result()`.
2. The container can't download workbench files, so return each csv as the cell's output (`out['monthly']`, and so on) and save it to `data/setter-sets/<end date>/`. Commit and push.
3. Update the page: upload the three csvs as assets of https://claude.ai/artifact/AWv8pnwSTD3MixQGejukAy (Artifact publish with `asset: true`), then update the documents `datasets/monthly`, `datasets/weekly` and `datasets/buckets` with the new `source.url`, `source.name` and `updated.at` (ArtifactData `update`, pinned to their version). Change the page title in `dash/meta` and the header in `files/index.html` if the date range changed, and copy the stored `files/index.html` back to `dashboards/setter-sets/index.html` if anyone edited it in the page.
4. Tell Sheila in a line or two what moved.

Known limits:

- Close only, as of the run: later cancellations, merges and pipeline moves change old months on the next run. Each dated folder keeps what the page showed that day.
- Setter calls are pulled for the six setters only. A set whose only touch was another rep's call goes to nobody.
- If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop.
