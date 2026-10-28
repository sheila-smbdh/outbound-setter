# Handoff: Bali Welcome Series outbound, moving to Claude Code in the cloud

- **From:** Cowork session in the claude.ai Project "Bali Test (Welcome Series Outbound)", Sheila Xu (sheila@smbdealhunter.xyz)
- **To:** a Claude Code session in the cloud (claude.ai/code), working from a GitHub repo that holds this folder
- **Date:** Oct 20, 2026
- **Mission:** Keep Bali's daily scorecard and the Monday weekly fix check running exactly as they run today (same numbers, same cards, same delivery to Sheila), but driven from this repo in Claude Code instead of the claude.ai Project, and keep the Welcome Series outbound SOP and its tracking rules in one place.

## 1. What this is

Bali (Jabali Dumas) is a setter who calls SMB Deal Hunter's Welcome Series sign-ups: newsletter subscribers who filled out the Typeform and asked to be contacted. Round one ran Sep 16 to 28, 2026 and was audited call by call (`docs/background/round-one-readout.md`). Round two started Sep 30 with 7 fixes. Since Oct 13 his priorities are speed to lead (60% called within 15 minutes), dials (200 a day) and show rate (90% of the closer calls he sets actually show), with four handoff steps under show rate. Voicemail, text, double dial, pickup and connect are still tracked as compliance.

Every weekday at 8:45am ET a scheduled task pulls the previous dialing day from Close, computes the numbers, renders two PNG cards (a cover and a funnel card), saves a daily record, republishes the scorecard page and sends the PNGs to Sheila, who forwards them to Bali in Slack herself. Every Monday at 8:56am ET a second scheduled task writes a dated section into the leadership doc "Welcome Series Round Two: Weekly Fix Check". Both have run cleanly every day; the last runs were Oct 19 (daily for Fri Oct 16, weekly for Oct 12 to 16) and Oct 20 (daily for Mon Oct 19).

Worth knowing before you change anything: those two scheduled tasks already run as Claude Code cloud sessions. What moves is where their instructions and files live. Today they read everything from the claude.ai Project with the Projects tool; after this handoff they read it from this repo. The Close math does not move: it runs in the Composio remote workbench (Close API through `proxy_execute`) in both setups, because the Close MCP connector cannot bulk-pull calls.

## 2. Where everything lives

Everything a cold session needs is in this folder. The claude.ai Project stays the current source of truth until cutover (section 7).

| Path | What it is | Read in full? |
|---|---|---|
| `README.md` | This brief | Yes |
| `CLAUDE.md` | Standing rules for any Claude Code session in this repo | Yes |
| `docs/RUNBOOK.md` | The source of truth: daily run, weekly run, card contents, every counting definition, targets, baselines, known limits. Verbatim copy of the Project doc, Oct 20 | Yes |
| `docs/HANDOFF-daily-scorecard.md` | Locked decisions and open items for the scorecard, verbatim copy, Oct 20 | Yes |
| `docs/SOP-Setter-Welcome-Series-Outbound.md` | Snapshot of Sheila's live SOP Google Doc (Oct 20). Live doc: https://docs.google.com/document/d/1VYe_kNFBSYMKQ9MFQNmGnS4HP0pHsMWpR583gbKLczE/edit | Yes |
| `docs/RECORDINGS-TEST-2026-10-05.md` | How to download and transcribe Close call recordings in the workbench, plus Sheila's rulings from listening (Oct 6 and 7) | Skim; use when a count looks off |
| `docs/project-instructions.md` | Project writing rules and the locked round-one numbers | Yes (short) |
| `docs/background/` | Round-one readout, round-two call script, round-one definitions, the Sep 29 Slack message to Bali (the 7 fixes), the Close call-outcome setup steps | Only when you need history |
| `kit/bali_metrics.py`, `bali_cover.py`, `bali_show.py`, `bali_slack.py` | The Close collector and all metric logic. Run inside the Composio workbench, exec'd in that order | Read before any run |
| `kit/build.py`, `template.html`, `cover.html`, `manrope.b64` | Renderer: metrics JSON in, scorecard HTML + two PNGs + daily record out (Playwright/Chromium) | Read `build.py` |
| `sample/metrics-2026-10-16.json` + `sample/reference-render/` | The exact metrics behind the Oct 16 card, and the two PNGs this kit renders from it | Use for the render check |
| `prompts/current-scheduled-task-prompts.md` | The exact prompts of the two live scheduled tasks, with their IDs and schedules | Yes |
| `docs/ABANDONED-TYPEFORM.md`, `kit/bali_abandoned.py`, `kit/abandoned_build.py`, `prompts/abandoned-typeform-routine.md` | Bali's separate Abandoned Typeform card (test started Oct 21): rules, collector, renderer and the weekday routine that DMs it to Sheila | When working on that card |
| `docs/SETTER-TRACKER.md`, `kit/setter_tracker.py`, `prompts/setter-tracker-routine.md` | The daily Setter Follow-up Tracker (Google Sheet, one tab per setter, leads grouped by SOP next step): rules, collector and sheet writer, and its routine | When working on the tracker |
| `docs/SETTER-SETS.md`, `kit/setter_sets.py`, `data/setter-sets/`, `dashboards/setter-sets/` | The Setter Sets report (all six setters' inbound and outbound sets by month and week, Close next to the self-reported tracker, and the closers' bucket for each set): rules, collector, dated data snapshots and the dashboard page source | When updating the setter sets report |

Live resources outside the repo (reachable through connectors, not files):

| Resource | ID / link | Access |
|---|---|---|
| Close CRM | via Composio `close` toolkit, `proxy_execute` in `COMPOSIO_REMOTE_WORKBENCH` (default account `close_helper-flap`, Sheila) | Read only |
| Slack group DM (Sheila, Bali, Zain, Helen, Jay) | `C0C11LAF4DB`; Bali = `U0BP10N2WSU`, Sheila = `U0BM6J8KM32` | Read only, never post |
| Scorecard page (artifact) | https://claude.ai/artifact/4ByC6XFCYm94RFqu5TNugg | `read` before every republish |
| Weekly leadership doc (Claude Doc) | https://claude.ai/code/artifact/3bacf3a9-f7f7-408b-853f-380abda0a41d | Edit only the new week's section |
| Daily records history (Sep 30 to Oct 19) | claude.ai Project, `claude/bali-kit/daily/YYYY-MM-DD.json` | Not copied here (see section 6) |
| Bali's self-tracker | Google Sheet "Welcome Series Test" `1VJ4_Mqo1touv-DeEF5OazSP-26K97GwUSM7ngTqeNL4`, tab "Data Tracking" | Back-check only, never a source of numbers |

### How the tracking data is gathered (plain version)

All numbers come from Close. Nothing Bali self-reports changes a count.

1. **Calls** (`/activity/call/`, Bali's user id): every outbound call except 0-second `external` duplicates is a dial. Each call is classified by, in order, Bali's Close call outcome, then a note code (VM / NA / SCR / TALK), then the voicemail-drop disposition, then 45+ seconds = pickup. Inbound callbacks he answered count as pickups for bookings only, never as dials.
2. **New leads and speed to lead** (`/sequence_subscription/` on the "Welcome Series - Bali Test" workflow `seq_0XX3twr6enX8SbfMZILA8x`): the enrollment time is the sign-up time. Speed to lead = sign-ups 9am to 9pm ET called within 15 minutes.
3. **Follow-ups** (`/activity/sms/`, calls, `/activity/status_change/lead/`): voicemail, text, try 2, try 3 and double dial for people who didn't pick up on their first call; Do Not Contact leads are left out.
4. **Bookings** (`/activity/meeting/`): a closer call is a meeting on one of the 13 closers' calendars created within 24 hours of a Bali pickup with no other rep's call in between; a self-set is a meeting on Bali's own calendar.
5. **Show rate and handoff steps** (`/activity/custom/` for the closer's "002) Discovery Call" outcome and Bali's "001) Pre-Discovery Call" notes, `/activity/status_change/opportunity/`, `/activity/email/`, `/activity/note/`): showed or not per lead set, plus the handoff email, closer note, day-before and morning-of reminders.
6. **Closes** (`/opportunity/` Won since Sep 16) on leads Bali sourced. **Duplicates** (`/lead/` by shared phone or email) are flagged to Sheila only.
7. **Slack cross-check**: Bali posts one note per real conversation in `C0C11LAF4DB`; `bali_slack.py` checks each note against Close and flags mismatches. Cross-check only.

The exact rules, with every edge case Sheila has ruled on, are in `docs/RUNBOOK.md` under "Definitions".

### The SOP in one paragraph

Call every Welcome Series lead within 15 minutes of the Typeform, newest first, from a US caller ID, Power Dialer off. Open without introducing yourself and end on a question; to screeners say only "Hey, it's [first name]". Qualify on goal, timeline and capital; serious leads go to a closer (then all four handoff steps: handoff email right after booking, setter notes in Close by end of day, reminder the day before, morning-of reminder if no reply), promising ones to the setter's own calendar, and pause the workflow on any booking. No answer: double dial, voicemail, text right away; dial again later that day; dial again the next day. Log a call outcome on every call. The full text is `docs/SOP-Setter-Welcome-Series-Outbound.md`.

## 3. Decisions locked (do not re-litigate)

All of `docs/HANDOFF-daily-scorecard.md` section 3 stands. The ones most likely to be second-guessed:

- **Counting rules are frozen.** Targets: speed 60%, dials 200, show rate 90%; compliance pickup 25%, connect 10%, voicemail 85%, text 85%, double dial 85%. Real conversation, closer call, show rate and handoff-step rules are as written in the runbook. Change none of them without Sheila saying so.
- **Two images only** (cover and funnel card), no detail card, no cover footnote (Sheila, Oct 14).
- **Delivery goes to Sheila, never to Bali.** Never post to Slack or message Bali; Sheila forwards the PNGs herself.
- **Bali's Slack notes are a cross-check only.** They never change a number.
- **Close stays read-only.** No writes to Close, Slack, the SOP doc or the self-tracker.
- **The Close pull stays in the Composio workbench.** Do not switch to the Close MCP connector for the bulk pull.
- **Saved daily records keep what Bali saw that morning.** Do not rewrite old records when Close changes later; the weekly report reruns `week()` for corrected numbers.
- **Writing:** no em dashes; never say leads "clicked on the site"; copy changes to docs go to Sheila as redlines (old and new).
- **The weekly report has no show rate** and still measures speed over the dialing window. Ask Sheila before changing either.
- **This move changes the plumbing only** (where files live, where records are saved, how the runs are scheduled), not what Bali or leadership see.

## 4. Changed since the last handoff doc (Oct 15)

- **The kit in this folder was checked on Oct 20.** `build.py` + `template.html` + `cover.html` + `manrope.b64` rebuilt the published Oct 16 page byte for byte from `sample/metrics-2026-10-16.json`. `bali_metrics.py` was run live in the Composio workbench for Oct 16 and matched the saved record on dials 88, people 54, pickups 20, real conversations 12, first-call no-pickups 30, voicemail 23 of 27, text 26 of 30, double dial 23, try 3 0 of 59. `bali_cover.py`, `bali_show.py` and `bali_slack.py` were copied from the Project by hand and compile, but have not been run from this copy yet: the parity run in section 7 is what proves them.
- **Close moved under the Oct 16 card.** A rerun now finds 4 closer calls for Oct 16, not the 5 on the card: Dishan De Silva's meeting with Jordan Zadrozny was canceled after the card went out (title "Canceled: ...", status declined-by-org). Expected drift, not a bug. Expect the same kind of small gaps in any parity check.
- **New records since Oct 15:** daily records for Oct 15, 16 and 19 are saved in the Project; the weekly section for Oct 12 to 16 was written Oct 19.
- **Sheila wrote a new SOP** ("Setter Welcome Series Outbound SOP", created Oct 19, edited Oct 20). It replaces Jay's v1 "Welcome_Series_SOP_Speed_to_Lead.md". Three gaps between it and the code, all open questions for Sheila, none to fix on your own:
  1. It links the Welcome Series workflow `seq_6T4cQDe4oxhEh6LKVlCutV`; the scorecard counts new leads from the Bali Test workflow `seq_0XX3twr6enX8SbfMZILA8x`. If Bali's leads start arriving through the general workflow, new-lead and speed numbers will drop to zero or undercount.
  2. Its outcome list has "Conversation: not a fit" and "Call screener: didn't get through" and no "Disqualified" or "Do not contact". The code counts "Disqualified" as a real conversation (60+ sec) and any "Conversation: ..." as a pickup, but "Conversation: not a fit" is not on the real-conversation list (`REAL_TAGS` in `bali_metrics.py`). If Bali switches to "not a fit", his DQ conversations stop counting toward connect rate.
  3. It ends with "Think about tracker for Jordan/Jose/Bali leads": a multi-setter tracker is being considered. The separate "Setter handoff check" task (another Project, `claude/setter-handoff-kit/`) already covers Bali, Jose Rodriguez and Jordan Kempster for call-script and handoff compliance. Out of scope here.
- **Still open from the recordings test (Oct 6 and 7):** Sheila ruled that Matt Weiss (Oct 5) and Dan Housley (Oct 6) were not Bali's sets, and a proposal to count a closer call only after a real conversation (60+ sec tagged or 3+ min untagged) is waiting for her answer. The code still credits those patterns.
- **Sheila's local folder** `welcome-series-readout-handoff/bali-coaching/HANDOFF-daily-scorecard.md` is a stale Sep 30 copy. Use `docs/HANDOFF-daily-scorecard.md` here.

## 5. Blockers and unblock paths

| Blocker | Who clears it | Exact action |
|---|---|---|
| The repo does not exist yet | Sheila | Create a private GitHub repo (for example `sheila-smbdh/bali-welcome-series`), unzip this package at its root, push, and open it in Claude Code on the web |
| Connectors in the Claude Code session | Sheila (receiving session checks) | The session needs Composio (with the `close` toolkit connected) and Slack. If either is missing, Sheila adds it in claude.ai connector settings. Without Composio nothing runs; without Slack only the cross-check is skipped |
| Where daily records and PNGs go | Sheila decides, receiving session asks (first move 2) | Keep writing records to the Project if the session has the Projects tool; otherwise commit them to `records/daily/` in the repo. PNGs keep going to Sheila through the chat if SendUserFile exists; otherwise ask her |
| Rendering needs Playwright + Chromium | Receiving session | `python3 -c "import playwright"`; if missing, `pip install playwright` and `python3 -m playwright install chromium` (needs the network allowlist to reach PyPI and the Playwright CDN; if blocked, tell Sheila which host) |
| Composio "API key revoked or expired" | Sheila | Reconnect the Composio connector in Claude's settings. The session says so plainly and stops |
| Old and new runs both firing | Sheila | After one clean parity day, pause or update the two old scheduled tasks (section 7). Never let both deliver on the same morning |
| PNGs can't be auto-posted to Slack | Org owner (only if Sheila ever wants auto-posting) | Allowlist files.slack.com under Admin settings > Capabilities. Today she forwards them herself, by choice |

## 6. What is not in this package, on purpose

- **The daily record history** (Sep 30 to Oct 19, about 25 KB each) stays in the Project. The runbook says weekly numbers come from rerunning `week()`, not from old records, so nothing breaks without them. If Sheila wants the history in the repo, copy them over from a session that has the Projects tool.
- **Secrets.** There are none in this package and none should ever be added. Close access lives in Sheila's Composio connection; Slack access in her Slack connector.

## 7. First moves, in order

1. Read this README, `CLAUDE.md`, `docs/RUNBOOK.md`, `docs/HANDOFF-daily-scorecard.md`, `docs/SOP-Setter-Welcome-Series-Outbound.md` and `prompts/current-scheduled-task-prompts.md` in full, and skim the four `kit/*.py` files. Tell Sheila in two or three lines what you loaded and which of these you can reach from this session: the Composio workbench, the Slack connector, the Projects tool, the Artifact tool, SendUserFile, Claude Docs, and scheduled-task tools. Say plainly if any is missing.
2. Ask Sheila these gating questions in one go, with tappable options, before running anything:
   - Daily records: keep saving to the claude.ai Project (recommended while the Project exists), or commit to `records/daily/` in this repo?
   - Cutover: update the two existing scheduled tasks to read from this repo (recommended: keeps their IDs and history), or create new ones and pause the old?
   - Which of the three SOP gaps in section 4 she wants raised now (workflow ID, "not a fit" outcome, multi-setter tracker), or leave all three for later?
3. Render check (no Close needed): `cd kit && python3 build.py ../sample/metrics-2026-10-16.json /tmp/out`. The two PNGs must look the same as `sample/reference-render/`. Look at both images once.
4. Parity run against Close for the most recent dialing day that has a saved record (Mon Oct 19 is the latest as of this writing). Follow the runbook "Daily run" steps 1 to 4, but write the workbench copies from `kit/` (compare md5 first; the four files must match this repo) and do not save the record, republish the page or send anything. Compare the top-line numbers with the saved record (`claude/bali-kit/daily/2026-10-19.json` in the Project, if reachable) and explain every difference: Close edits after the morning run (cancellations, merges, late outcomes) are expected; anything else is a bug to fix before cutover.
5. Show Sheila the parity result in a few lines and the two PNGs. Get her OK.
6. Cut over the way she chose in move 2. If you update the existing tasks, change only the file-reading steps of the prompts in `prompts/current-scheduled-task-prompts.md` ("read claude/bali-kit/... with the Projects tool" becomes "read ... from the repo"), keep everything else word for word, and keep the schedules (`CRON_TZ=America/New_York 45 8 * * 1-5` and `CRON_TZ=America/New_York 56 8 * * 1`). Make sure only one daily and one weekly task are enabled afterwards.
7. Watch the first live morning (and the first Monday) and confirm to Sheila in one line that it delivered.

## 8. Done means

- One daily and one weekly scheduled task are enabled, both reading their instructions and kit from this repo, on the same schedules as today.
- The first live daily run after cutover delivered the two PNGs and the Sheila-only lines (Slack check, duplicates, show rate) with numbers that match a Close rerun, and saved its record where Sheila chose.
- The first Monday after cutover wrote a new week section in the leadership doc and sent Sheila the link with the one-sentence verdict.
- No counting rule, target or card layout changed.
- Sheila has a one-line note saying the move is done and where the records now live.
