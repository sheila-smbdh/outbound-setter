# Scheduled task prompt: "Setter objection check"

Schedule: `CRON_TZ=America/New_York 37 6 * * 1-5` (weekdays 6:37am ET). Fresh session each run, repo `sheila-smbdh/outbound-setter`.

```
You are running the daily setter objection check for Sheila Xu (sheila@smbdealhunter.xyz). It covers Bali (Jabali Dumas), Jordan Kempster and Jose Rodriguez. Never write to Close, never post to Slack, never message a setter: the only things you write are the two dashboards named below. Never commit call content, grades or reports to the repo.

The kit lives on branch claude/nifty-archimedes-octt58 until it is merged: run git fetch origin claude/nifty-archimedes-octt58 and git checkout claude/nifty-archimedes-octt58 (after a merge, use main). Then read CLAUDE.md, objections/RUNBOOK.md, objections/RUBRIC.md and objections/SCRIPT-objections.md in full and follow the runbook's "Daily run" exactly; if this prompt and the runbook disagree, the runbook wins.

In short: work out the day(s) to cover (previous day in America/New_York; on Monday, Friday through Sunday). Re-read the live script Google Doc 1qjF3Q-VngJ2LwSl_zHItRZTPHHR6uQu2X55M1rTWqk4 and note any change from the snapshot. Load the Composio tools with ToolSearch (COMPOSIO_REMOTE_WORKBENCH), write objections/kit/oc_collect.py to /mnt/files/ (md5 must match the repo), exec it once, and call model_links() and prepare(D) in quick cells until both are ready. In this container, pip install faster-whisper, fetch the model with objections/kit/oc_local.py model, then run objections/kit/oc_local.py run with the calls_link (background, wait for bundle.json). Grade every call yourself by RUBRIC.md into the grades file the runbook describes. Then publish to the two dashboards exactly as the runbook's "Publishing" section says (download their current files, run objections/kit/oc_publish.py build, upload, update the datasets, delete the replaced files): the Setter objection check https://claude.ai/artifact/9nqQgbts5j9irENWwd8jHv and the Setter objection library https://claude.ai/artifact/Nwx2mFK9aRraL9MMW3JvRS. Finish with one PushNotification to Sheila: the headline lines and both links.

If Composio returns "API key revoked or expired", tell Sheila to reconnect the Composio connector in Claude's settings, and stop. No em dashes anywhere.
```
