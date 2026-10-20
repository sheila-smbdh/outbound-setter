# Handoff: Bali's daily scorecard

> Copied verbatim from the claude.ai Project doc `claude/bali-kit/HANDOFF-daily-scorecard.md` on Oct 20, 2026. Its decisions still stand; the top-level `README.md` of this package says what changed since and how the runs map to Claude Code.

**Last updated:** Oct 15, 2026 (fourth handoff step under show rate: "Closer note attached", Bali's background note on the lead in Close by the end of the booking day). Oct 14: (two images only: cover and funnel card; detail card hidden; no footnote on the cover). Oct 13: (v4, Sheila: priorities on top are speed to lead, dials and show rate with the three handoff steps; pickup, connect, voicemail, text and double dial moved to a compliance section at the bottom, voicemail/text/double dial on one row; callbacks Bali answers count for closer calls). Previous: Oct 8 (Do Not Contact, duplicates, text denominator, closer split, two-step closer calls); Oct 6 (Slack cross-check; closer-call fix for 0-second external records; v3.4 blue "Set to a closer" tile); Oct 5 (v3.1 Connect tile, v3.2 voicemail KPI, v3.3 real-conversation rule); Sep 30 (scorecard v3 approved)
**For:** any Cowork session in the project "Bali Test (Welcome Series Outbound)", working with Sheila Xu
**Mission:** Own Bali's daily scorecard. Make sure the automatic weekday run works, fix it when it breaks, and make any changes Sheila asks for without changing how the numbers are counted.

Read `claude/bali-kit/RUNBOOK.md` in full first. It is the source of truth for the daily and weekly procedures, the card contents, the definitions, targets and baselines. This file only adds context and decisions.

## 1. What this is

Bali (Jabali Dumas) is a setter who calls Welcome Series sign-ups. Round one ran Sep 16 to 28, 2026. On Sep 29 Sheila gave him 7 fixes, effective Wed Sep 30: newest leads first within 15 minutes; a US caller ID; Power Dialer off; SOP section 6 on no-answers; the new opener; "Hey, it's Bali" to screeners; a code (VM, NA, SCR, TALK) at the start of every call note. On Oct 13 she shifted his focus: he had done well on voicemail, text, double dial, pickup and connect, so the priorities became speed to lead, dials and show rate (the closer calls he sets should show up), driven by three handoff steps.

The scorecard is how Bali sees whether he's doing it. Each weekday morning Sheila gets two PNGs (cover and summary/funnel card; the detail card was dropped Oct 14) and posts them to Bali in Slack herself. The first real scorecard was Thu Oct 1 (covering Wed Sep 30). The first v4 card is Wed Oct 14 (covering Oct 13).

## 2. Where everything lives

| Resource | What it is |
|---|---|
| `claude/bali-kit/RUNBOOK.md` | Procedures, card contents, definitions, targets, baselines, known limits. Read in full |
| `claude/bali-kit/bali_metrics.py` | Close pull and metric logic (v2 base; Oct 5: 13 closers, DQ as pickup, `no_vm_option`, `is_real_call`; Oct 6: `other_rep_call`; Oct 8: Do Not Contact, two-step; Oct 13: `inbound_talk`, callbacks in `_bookings`). Runs in the Composio remote workbench (`proxy_execute`, `close` toolkit). `run(date)` = daily, `week(start,end)` = weekly |
| `claude/bali-kit/bali_cover.py` | Cover metrics (v3). Exec after `bali_metrics.py`. `run_cover(date)` |
| `claude/bali-kit/bali_show.py` | Show rate and handoff steps (v4, Oct 13). Exec after `bali_cover.py`. The daily run calls `run_show(D, run_cover(D))` |
| `claude/bali-kit/bali_slack.py` | Slack cross-check (Oct 6). Exec last. `slack_check(D, msgs)` daily, `slack_week(days, msgs)` weekly. Changes no metric |
| `claude/bali-kit/build.py`, `template.html`, `cover.html`, `manrope.b64` | Build the page, three PNGs and the daily record in the Claude container. Targets, groups (`PRIORITY`, `COMPLIANCE`), the yellow rule, `show_row()`, `STEP_FIX` and `track_tiles()` live in `build.py` |
| `claude/bali-kit/daily/YYYY-MM-DD.json` | One saved record per dialing day, written by the daily run (from Oct 6 on, with a `track` entry; from Oct 7 on, with `metrics.slack_check`; from Oct 14 on, with `metrics.show`) |
| Artifact https://claude.ai/artifact/4ByC6XFCYm94RFqu5TNugg | "Bali's Daily Scorecard". Always `read` it before republishing |
| Slack group DM `C0C11LAF4DB` | Where Bali posts a note per real conversation since Oct 5. Bali = `U0BP10N2WSU`, Sheila = `U0BM6J8KM32`. Read only; never post there |
| Scheduled task `trig_019kHkq8cfowh57PwF7hRT4M` "Bali daily scorecard" | `CRON_TZ=America/New_York 45 8 * * 1-5`, auto approvals, push on. Prompt updated Oct 13 for v4 (four scripts, `run_show(D, run_cover(D))` in a thread, show line for Sheila); it pulls all build files fresh from the project |
| Scheduled task `trig_01J9xMRjieK9z92JxLXn8EVp` "Bali weekly fix check" | Mondays 8:56am ET, writes the leadership doc https://claude.ai/code/artifact/3bacf3a9-f7f7-408b-853f-380abda0a41d from `week()`. Not changed for v4 (no show rate in the weekly yet) |
| `claude/project-instructions.md` | Project writing rules (no em dashes, never "clicked on the site", redlines for doc copy) |

Close IDs: Bali `user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl`; Bali Test workflow `seq_0XX3twr6enX8SbfMZILA8x`; Sheila's Slack self-DM `D0BLE68V517`. Handoff email template "Setter to Closer Handoff" `tmpl_GfFgB6tt3nD6WaAsfgT3R8ZyuRvR8x9PtryCNr2oDN2`. Closer's post-call activity "002) Discovery Call" `actitype_4mIZqROw9obY6LQWDvGdtn`, Call Outcome field `cf_d6Xh2R1rxhHkMoo76I3O19HJCVbdrmeSczYD1bpV1IK`.

## 3. Decisions locked (do not re-litigate)

- **Audience:** Bali-facing, plain and warm. Leadership detail goes in the weekly doc.
- **Delivery:** PNGs go to Sheila, never to Bali.
- **Cover first (Sep 30):** bottom line on its own page. Summary and detail cards stay as they were.
- **v4 layout (Sheila, Oct 13):** priorities on top: Speed to lead and Dials stacked on the left, Show rate on the right with "All calls you've set since Sep 16" and the three handoff steps under it. Header: "You hit X of 3 priority targets". Bottom section "Keep it up: compliance we still track": Voicemail, Text, Double dial on one row (Sheila asked for that row specifically), then Pickup rate, Connect rate and the blue Set to a closer tile.
- **Targets:** speed to lead 60%, dials 200, show rate 90% (Oct 13); compliance: pickup 25%, connect 10%, voicemail 85%, text 85%, double dial 85% (all three lowered from 100% by Sheila, Oct 14).
- **Show rate (Sheila, Oct 13):** strictly calls showed / calls he set to a closer. Main number = last 7 days; under it, every call set since Sep 16. **Reschedules wait:** a rescheduled call counts on its new date. No-shows, cancels and reschedule requests with no new time count as not showed. One per lead. Outcome comes from the closer's Discovery Call activity; a call with nothing logged is left out and listed for Sheila (not counted against Bali).
- **Handoff steps (Sheila, Oct 13):** 1) the Setter to Closer Handoff email (template in Close) right after booking (we allow 60 minutes); 2) a reminder the day before the call; 3) a personal reminder the morning of the call if the lead hasn't responded. Shown on the show rate tile as done of due over the last 7 days, counted from Oct 13. **Oct 15 (Sheila):** a fourth step, 4) "Closer note attached": Bali writes the lead's background in Close (a note, a call note or his Pre-Discovery Call form notes, 40+ characters) by the end of the booking day, so the closer can read it before the call. Sheila offered Bali a Loom if he needs one on the email.
- **Callbacks count (Sheila, Oct 13):** a callback Bali answers counts as a pickup for closer calls, self-sets, sets so far, closes and show rate. Not a dial. Found with Danny Berger (Oct 13, set to Nick Vaughan off an inbound callback after Bali's voicemail).
- **Fixes list (v4):** handoff steps missed that day (by lead), then speed/dials/show rate misses worst first, then any compliance number in red. (Replaces the Sep 30 rule that fixes covered only voicemail, text and double dial.)
- **Pickup vs connect (Oct 5):** both shown as separate tiles; connect = `real_conversations / people_dialed`.
- **Set to a closer tile (v3.4, Oct 6):** blue, tracked only, no target, not in the targets count, no fix line. Split by first call (Oct 8). New tracked numbers go in `track_tiles()`.
- **Real conversation (v3.3, Oct 5):** 60+ sec tagged Set to closer, Call back later or Disqualified, or Set to self only when a meeting was actually booked; untagged calls 3+ min or booked.
- **Bali's Slack notes (Oct 6): cross-check only.** Never change a count.
- **Closer call and 0-second external records (Oct 6):** don't block the closer-call credit.
- **Voicemail KPI (v3.2, Oct 5):** counted only out of no-pickups who gave him a chance to leave one.
- **Colors:** green = hit, yellow "Almost" = 75%+ of target, red = missed, blue = tracked with no target, gray = no calls due (show rate only).
- **Speed to lead window:** sign-ups 9am to 9pm ET, on the cover and the detail card. When the number moves between definitions, explain it with a split by time segment.
- **Closes:** cumulative Won deals from Bali-sourced closer calls since Sep 16, one per lead. 1 as of Oct 13 (Jim Montgomery).
- **US number win:** shown only on the day he switches (Sep 30).
- **Best time to dial** on the detail card stays searched across 9am to 11pm ET.
- **Emphasis on new leads** on the summary funnel. Don't add back the backlog size, "tomorrow starts with" box or older-leads breakdown.
- **Two images, no cover footnote (Sheila, Oct 14):** the page was too long. Don't bring back the detail card or the footnote unless she asks. Same day she also dropped the win of the day / one fix boxes from the funnel card (hidden by CSS in `cover.html`).
- **Writing:** no em dashes; never "clicked on the site".

## 4. Open items as of Oct 13

1. The summary card's single fix still uses the old rule order. Sheila hasn't said whether it should follow the cover's v4 priorities.
2. The weekly report still measures speed to lead over the dialing window, and has no show rate. Ask before changing either.
3. Composio workbench copies of the scripts disappear when Composio starts a fresh workbench; each run rewrites them from the project copies (now four: `bali_metrics.py`, `bali_cover.py`, `bali_show.py`, `bali_slack.py`). The workbench is shared: on Oct 13 a helper (`_q`) was found overwritten mid-session; re-exec the files if a helper misbehaves.
4. Close call outcomes went live Sep 30. If Close adds or renames call outcomes, check `classify()`, `no_vm_option()` and `is_real_call()`. If closers rename Discovery Call outcomes or opportunity statuses, check `NOT_SHOWED`, `SHOWED_OPP` and `NOSHOW_OPP` in `bali_show.py`.
5. PNGs can't be auto-posted to Slack (files.slack.com blocked by the egress proxy).
6. **Unlogged closer calls (Oct 13):** Denise McGuire (Owen Henderson, Oct 6; Owen emailed "Reschedule Call / Resources" 25 minutes after the start, so likely a no-show) and Kirk Gage (Owen, Oct 12, meeting declined from Owen's side) have no Discovery Call outcome. They're left out of show rate until logged; the daily show line lists them for Sheila.
7. **Before Oct 13 Bali sent his "Info Packet" email after booking** (template `tmpl_CEBk...`, "Setter Resources - Omar"), never the handoff template, and sent no reminders of his own (closers send their own confirmations and reminders). His first handoff email was Danny Berger, Oct 13, 2 minutes after the booking.
8. **Gareth Cheng** (Oct 8 set) appears twice in sets so far (Oct 8, and Oct 9 as "Gareth/Daniel SMB Deal Hunter Reconnect", a 15-min reconnect Daniel booked after Bali reached him again). Show rate counts the lead once. Sets so far still counts both; Sheila hasn't been asked.
9. Back-check vs Bali's self-reported sheet "Welcome Series Test" (1VJ4_Mqo1touv-DeEF5OazSP-26K97GwUSM7ngTqeNL4), tab "Data Tracking": row 13 = dials (matches Close's raw outbound count incl. external duplicates), row 17 = his own judgment of real conversations (about 1.6x ours), rows 20/23/26 = self-sets, closer sets, DQ'd.
10. Close has recordings for most calls but no transcripts, and the recording URL isn't reachable through `proxy_execute`. Judge on duration, outcome, note, bookings and his Slack note.
11. Before writing any kit file, `project_read` it fresh and build on that copy; never write from an older local copy (two sessions edited the kit at once on Oct 5 and Oct 6).

## 5. Tone

Keep the machinery out of Sheila's face. The conversation stays about Bali and his calls. Give her a one-line note of what changed or what was checked, never a status dump.
