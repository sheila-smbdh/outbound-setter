# Handoff: build a setter scorecard for another team, modeled on Bali's

**From:** Claude Code session in the repo `sheila-smbdh/outbound-setter` (Sheila Xu, sheila@smbdealhunter.xyz), Nov 2, 2026
**To:** a fresh Claude session (Claude Code on the web recommended, see section 5) run by a coworker of Sheila's who is building something similar for a different team
**Mission:** Build a daily setter scorecard for the coworker's team by reusing the method, the code patterns and the lessons of Bali's Welcome Series scorecard, with the coworker deciding that team's KPIs, targets and audience.

Read this whole file first. Everything it points to is in the `reference/` folder next to it (a copy of Sheila's repo as of Nov 2, 2026). You do not need access to Sheila's GitHub repo or her claude.ai Project.

---

## 1. What this is

Sheila runs a daily scorecard for Bali (Jabali Dumas), a setter who phones SMB Deal Hunter's Welcome Series sign-ups (newsletter subscribers who filled out the Typeform and asked to be contacted). Every weekday at 8:45am ET a scheduled Claude task pulls the previous dialing day from Close CRM, computes his numbers, renders two PNG cards (a cover with his priorities and a funnel card), saves a daily JSON record, republishes a scorecard web page, and sends the PNGs to Sheila. She forwards them to Bali in Slack herself. A second task writes a weekly section for leadership every Monday. It has run since Sep 30, 2026, through about ten rounds of rule changes, all ruled on by Sheila.

The coworker wants the same kind of thing for another team in the org. This handoff is NOT about running or changing Bali's scorecard. It hands over the blueprint: how the data is pulled, how each number is defined, how the cards are built and delivered, and the traps that took weeks to find. Your job is to adapt that blueprint, not to copy Bali's numbers or rules blindly. A different team will have different people, a different lead source, maybe different KPIs, and its own owner who rules on the edge cases.

The most valuable thing in `reference/` is not the code; it is `reference/docs/RUNBOOK.md`, section "Definitions". Every line there is an edge case someone hit with real data. Read it as a checklist of questions to ask the coworker about their team.

## 2. Where everything lives

All paths are inside this handoff folder.

| Path | What it is | Read in full? |
|---|---|---|
| `README.md` | This brief | Yes |
| `reference/docs/RUNBOOK.md` | Source of truth for Bali's scorecard: daily and weekly run steps, what the cards show, every counting definition, targets, known limits | Yes, especially "Definitions" and "Known limits" |
| `reference/docs/HANDOFF-daily-scorecard.md` | Locked decisions and open items for Bali's card, with the reasons | Yes |
| `reference/BALI-README.md` | The Oct 20 brief that moved Bali's scorecard into a repo. Has the plain-English "How the tracking data is gathered" list | Yes, sections 1 and 2 |
| `reference/BALI-CLAUDE.md` | The standing rules file for Bali's repo. A good template for the new repo's `CLAUDE.md` | Yes (short) |
| `reference/prompts/current-scheduled-task-prompts.md` | The exact prompts of the two scheduled tasks (daily and weekly). Template for the new team's scheduled task | Yes |
| `reference/docs/SOP-Setter-Welcome-Series-Outbound.md` | Bali's setter SOP. Shows how the KPIs map to the behaviors in the SOP | Skim |
| `reference/kit/bali_metrics.py` | The Close collector and core metrics: dials, pickups, real conversations, speed to lead, follow-ups, bookings. Entry points `run(date)` and `week(start, end)` | Read before writing any collector |
| `reference/kit/bali_cover.py`, `bali_show.py`, `bali_slack.py` | Cover metrics and duplicates check; show rate and handoff steps; Slack cross-check | Skim; read the one you reuse |
| `reference/kit/build.py`, `template.html`, `cover.html`, `manrope.b64` | Renderer: metrics JSON in, HTML page + PNGs + daily record out (Playwright/Chromium). Targets, colors and tile groups live at the top of `build.py` | Read `build.py` |
| `reference/sample/metrics-2026-10-16.json` + `reference/sample/reference-render/*.png` | A real metrics JSON and the two cards it renders to. Look at the PNGs first to see the target product | Look at the PNGs |
| `reference/docs/RECORDINGS-TEST-2026-10-05.md`, `reference/docs/background/` | History: recordings test, round-one readout, Close call-outcome setup steps | Only if needed |

Note: the reference files contain real lead names and Close IDs from Bali's team. They are internal; keep them inside the org and do not paste them into anything public.

## 3. Decisions locked (do not re-litigate)

These are the design choices that held up for Bali. Keep them unless the coworker explicitly decides otherwise for their team.

- **Close is the only source of numbers.** Self-reported trackers and Slack notes are a cross-check at most; they never change a count. (Bali's own sheet ran about 1.6x higher on "real conversations" than Close.)
- **Read-only everywhere.** The scorecard never writes to Close, never posts to Slack, never messages the setter. Delivery goes to the manager, who forwards it. This keeps a human between the machine and the rep.
- **Bulk Close pulls run in the Composio remote workbench** (`COMPOSIO_REMOTE_WORKBENCH`, `proxy_execute` with the `close` toolkit), in Python, in a thread because the workbench cell limit is 180 seconds. The Close MCP connector cannot bulk-pull calls. In a Claude Code cloud session where the Close REST API is reachable directly (inline `curl` to `api.close.com`), that also works for reads; follow whatever Close-access rules the coworker's own `CLAUDE.md` sets.
- **A daily record is saved the morning it is sent and never rewritten.** It shows what the rep saw. Corrected numbers come from rerunning the metrics for a date range, not from editing old records.
- **Every definition is written down in a runbook before it ships,** with the date and who ruled on it. Code constants (targets, closer list, outcome names) live in one place each.
- **Few numbers, ranked.** Bali's card shows 3 priorities on top and the rest as "compliance we still track" at the bottom. Green = hit, yellow "Almost" = 75%+ of target, red = missed, blue = tracked with no target.
- **Two images, no footnote.** Sheila cut a third card and a definitions footnote because the page got too long.
- **Writing:** no em dashes; never say leads "clicked on the site". Propose copy changes to any shared doc as redlines (old and new).

## 4. Lessons learned the hard way (check each one against the new team's data)

1. **Close double-logs calls.** 0-second `call_method = external` records sit next to real calls. Exclude them from dials, and don't let them count as "another rep's call" either. Close's own reports page counts them, so the rep's number will look higher than yours; have the explanation ready.
2. **Call classification order matters:** the rep's Close call outcome first, then a note code, then the voicemail-drop disposition, then call length (45+ seconds = pickup) only if nothing else exists.
3. **"Real conversation" needs a floor.** Outcome tags alone over-count; Bali's rule is a 60+ second call with a conversation tag, or 3+ minutes if untagged, and "set to self" only counts if a meeting was actually booked.
4. **Voicemail rate needs the right denominator:** only no-pickups where the rep could leave one (busy, blocked, failed and very short hang-ups are left out).
5. **Credit for a booking:** a closer's meeting created within 24 hours of the setter's pickup with no other rep's call in between. Leads who booked themselves before the setter ever dialed are not the setter's set. A lead first set to the setter's own calendar and later handed to a closer still counts. Callbacks the setter answers count for bookings but are never dials.
6. **Show rate depends on closers logging the outcome.** A past meeting with nothing logged is left out and listed for the manager, not counted against the setter. A rescheduled call counts on its new date.
7. **Duplicates and merges move numbers after the fact.** Flag duplicate leads (same phone last 10 digits, or same email) to the manager; expect reruns to differ slightly from the morning card.
8. **Leads set to Do Not Contact** drop out of follow-up denominators.
9. **The Composio workbench is shared and gets recreated.** Scripts there can vanish or be overwritten by other sessions. Every run rewrites them from the repo copy (compare md5 first) and rebuilds any input variables in the same run.
10. **Two sessions once edited the same kit files at once.** Pull the latest before any edit.
11. **Composio "API key revoked or expired"** means the person reconnects the Composio connector in Claude's settings; stop and say so, don't switch tools.
12. **The container can't upload to Slack (files.slack.com is blocked) or download Composio files (backend.composio.dev is blocked).** Return workbench output as the cell's output; deliver PNGs to the manager through Claude.

## 5. Blockers and unblock paths

- **Which surface:** owned by the coworker. Claude Code on the web (claude.ai/code) is recommended: it can run Python and Playwright to render the cards, commit to a repo, and create scheduled tasks. Cowork or chat can design the KPIs and read Close but cannot render or schedule. If on Claude Code, upload this folder into a new GitHub repo of their own first.
- **Close access through Composio:** owned by the coworker. Connect Composio in claude.ai connector settings and connect its `close` toolkit with their own Close login. Without it, bulk call pulls do not work. Their Close user needs read access to the team's leads, calls and meetings.
- **The new team's facts:** owned by the coworker (and their team lead). The session cannot guess these: the setter(s) and their Close user IDs, the lead source (Close workflow/sequence ID or smart view), who the closers are, the KPIs and targets, who receives the card, the schedule. Gathered in first moves 2 and 3.
- **Slack cross-check, if wanted:** owned by the coworker. Needs the Slack connector; skip it otherwise.
- **Questions about how Bali's version works:** Sheila Xu (owner). For anything about the Claude setup itself, Zain.

No secrets or API keys are in this package, and none should be added. Close access lives in the person's own Composio connection.

## 6. First moves, in order

1. Read this README, then `reference/docs/RUNBOOK.md`, `reference/docs/HANDOFF-daily-scorecard.md`, `reference/BALI-README.md` (sections 1 and 2), `reference/prompts/current-scheduled-task-prompts.md` and `reference/kit/build.py`, and look at the two PNGs in `reference/sample/reference-render/`. Tell the coworker in two or three lines what you loaded, and which tools you can reach from this session: Composio workbench with Close, direct Close API, Slack, Artifact, SendUserFile, scheduled tasks, a terminal with Python. Say plainly if any is missing.
2. Ask the coworker the gating questions, one at a time, with tappable options where they fit, before drafting anything:
   - Which team, which setter(s), and who will receive the scorecard (the manager forwards it, or the reps see it directly)?
   - What does the setter's job look like: inbound sign-ups like Bali, cold outbound, reactivation, something else? Where do their leads come from in Close (workflow, smart view, lead status)?
   - Which 2 to 4 numbers matter most right now, with targets? Offer Bali's set as a starting menu: speed to lead, dials, show rate, pickup rate, connect rate, voicemail, text, double dial, closer sets.
   - Daily, weekly, or both? What time, and in which time zone?
3. For each KPI they pick, walk the matching lines of the runbook "Definitions" and section 4 above, and ask how their team should rule on each edge case. Write the answers into a new `docs/RUNBOOK.md` for their team, dated, before writing code.
4. Build the collector by adapting `reference/kit/bali_metrics.py` (rename, swap IDs and constants, drop what they don't need). Run it read-only for one recent day and show the coworker the raw numbers with a handful of example leads, so they can spot-check against Close.
5. Adapt `build.py` and the HTML templates for their KPIs. Render one day and show the PNGs. Iterate on layout with them.
6. Once they approve a day's numbers and cards, set up the scheduled task, adapting `reference/prompts/current-scheduled-task-prompts.md`. Watch the first live run and confirm in one line that it delivered.

## 7. Tone

Keep the machinery (branches, workbench cells, md5 checks) out of the coworker's face; the conversation stays about their team and their reps' calls. Short updates, one decision at a time. When anything feels heavy: "If this feels hard or confusing at all, please reach out to Zain. He promises he wants to hear all about it, so he can make this feel like magic. Thank you for using it!"

## 8. Done means

- The new team has its own repo (or folder) with a runbook that defines every number on its card, each rule dated and owned by the coworker or their lead.
- A collector and renderer produce that team's cards from Close, read-only, and one real day has been spot-checked by the coworker against Close.
- A scheduled task delivers the cards to the agreed person at the agreed time, and the first live run was confirmed.
- Nothing in Bali's scorecard, repo or scheduled tasks was changed.
- The coworker gets a one-line note saying it is live and where the runbook lives.
