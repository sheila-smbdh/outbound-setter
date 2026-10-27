# Bali Welcome Series kit: rules for Claude

Read `README.md` first in every new session, then `docs/RUNBOOK.md` before any run. The runbook wins over any prompt when they disagree.

- Owner: Sheila Xu (sheila@smbdealhunter.xyz). Subjects: the Welcome Series setters Bali (Jabali Dumas), Jose Rodriguez and Jordan Kempster, one daily card each (runbook, "Three setters and the v5 cards").
- Read-only everywhere: never write to Close, never post to Slack, never message Bali, Jose or Jordan. Sheila forwards the scorecard herself.
  One exception (Sheila, Oct 22, 2026; was her own DM from Oct 21): the Abandoned Typeform card and its Close links message go to the Slack group DM C0C11LAF4DB (Sheila, Bali, Zain, Helen, Jay) and nowhere else. See `docs/ABANDONED-TYPEFORM.md`.
  Second exception (Sheila, Oct 22, 2026; was her own DM from Oct 21): the daily setter scorecards routine posts Bali's, Jose's and Jordan's cards to the Slack channel C0C9VANP6QN (Sheila, the three setters, Helen, Jay, Zain) and nothing else there; problems with the run go to Sheila's own DM (D0BLE68V517). See `prompts/setter-scorecards-routine.md`.
  Third exception (Sheila, Oct 27, 2026): the Setter Follow-up Tracker rewrites its own Google Sheet (`1R9G94XcDYBViugBPW0OEMBkueU1hHanedyyxaBn_lSU`, shared with the three setters) once a day and writes nothing else. See `docs/SETTER-TRACKER.md`.
- Close data comes through the Composio remote workbench (`proxy_execute`, `close` toolkit), not the Close MCP connector. Before exec'ing, make the workbench copies of `kit/bali_metrics.py`, `bali_cover.py`, `bali_show.py`, `bali_slack.py` match this repo (md5), then exec them in that order.
- Do not change counting rules, targets, the card layout or the SOP without Sheila's say-so. Propose doc copy changes as redlines (old and new).
- Before editing any kit file, pull the latest from the repo; two sessions once edited the same files at once.
- Writing: no em dashes anywhere; never say leads "clicked on the site". Keep messages to Sheila short and about Bali's calls, not the machinery.
- If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop.
- If anything feels hard or confusing, Sheila can reach out to Zain.
