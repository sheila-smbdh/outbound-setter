# Bali Welcome Series kit: rules for Claude

Read `README.md` first in every new session, then `docs/RUNBOOK.md` before any run. The runbook wins over any prompt when they disagree.

- Owner: Sheila Xu (sheila@smbdealhunter.xyz). Subject: Bali (Jabali Dumas), setter on Welcome Series sign-ups.
- Read-only everywhere: never write to Close, never post to Slack, never message Bali. Sheila forwards the scorecard herself.
  One exception (Sheila, Oct 21, 2026): the Abandoned Typeform card goes to Sheila's own Slack DM (D0BLE68V517) and nowhere else. See `docs/ABANDONED-TYPEFORM.md`.
- Close data comes through the Composio remote workbench (`proxy_execute`, `close` toolkit), not the Close MCP connector. Before exec'ing, make the workbench copies of `kit/bali_metrics.py`, `bali_cover.py`, `bali_show.py`, `bali_slack.py` match this repo (md5), then exec them in that order.
- Do not change counting rules, targets, the card layout or the SOP without Sheila's say-so. Propose doc copy changes as redlines (old and new).
- Before editing any kit file, pull the latest from the repo; two sessions once edited the same files at once.
- Writing: no em dashes anywhere; never say leads "clicked on the site". Keep messages to Sheila short and about Bali's calls, not the machinery.
- If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop.
- If anything feels hard or confusing, Sheila can reach out to Zain.
