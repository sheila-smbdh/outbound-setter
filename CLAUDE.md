# Bali Welcome Series kit: rules for Claude

Read `README.md` first in every new session, then `docs/RUNBOOK.md` before any run. The runbook wins over any prompt when they disagree.

- Owner: Sheila Xu (sheila@smbdealhunter.xyz). Subject: Bali (Jabali Dumas), setter on Welcome Series sign-ups.
- Read-only everywhere: never write to Close, never post to Slack, never message Bali. Sheila forwards the scorecard herself.
- Close data comes through the Composio remote workbench (`proxy_execute`, `close` toolkit), not the Close MCP connector. Before exec'ing, make the workbench copies of `kit/bali_metrics.py`, `bali_cover.py`, `bali_show.py`, `bali_slack.py` match this repo (md5), then exec them in that order.
- Do not change counting rules, targets, the card layout or the SOP without Sheila's say-so. Propose doc copy changes as redlines (old and new).
- Before editing any kit file, pull the latest from the repo; two sessions once edited the same files at once.
- Writing: no em dashes anywhere; never say leads "clicked on the site". Keep messages to Sheila short and about Bali's calls, not the machinery.
- If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop.
- If anything feels hard or confusing, Sheila can reach out to Zain.

## Setter objection check (separate daily report, Oct 25)

- `objections/` holds a second, separate routine: a daily objection-handling check for Bali, Jordan Kempster and Jose Rodriguez, graded from call recordings against the "Setter Inbound Call Script_Oct 2026". It publishes to two claude.ai dashboards (a daily scorecard for leadership and a growing objection library). Read `objections/RUNBOOK.md` before any objection run; it does not touch the Bali scorecard kit.
