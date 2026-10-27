# Routine: "Setter follow-up tracker" (daily, 8:41am ET)

Created Oct 26, 2026 at Sheila's request. Fires a fresh Claude Code cloud session every day at 8:41am ET (`CRON_TZ=America/New_York 41 8 * * *`). It rewrites the Google Sheet "Setter Follow-up Tracker" from Close and posts nothing anywhere. Trigger `trig_0138J4bhPa531diuJJrxQhEc`. Composio was added to it by Sheila in the claude.ai Routines settings (Oct 27). It reads `docs/SETTER-TRACKER.md` and `kit/setter_tracker.py` from main. The stored prompt is below, word for word. Its step 5 also says to stop if the Composio tools are missing.

```
You are refreshing the Setter Follow-up Tracker for Sheila Xu (sheila@smbdealhunter.xyz): a Google Sheet with one tab per Welcome Series setter (Bali, Jose, Jordan) listing every lead on their list grouped by the next step their SOP asks for. Read Close only. Write only to that sheet (id 1R9G94XcDYBViugBPW0OEMBkueU1hHanedyyxaBn_lSU). Never post to Slack, never message the setters, never write to Close, never edit or commit repo files.

1. Get the repo sheila-smbdh/outbound-setter: if it isn't already in the working directory, attach it with add_repo and clone it as add_repo says. Run git pull origin main, then read CLAUDE.md and docs/SETTER-TRACKER.md. If this prompt and that doc disagree, the doc wins.
2. Load COMPOSIO_REMOTE_WORKBENCH with ToolSearch. Make /mnt/files/bali_metrics.py and /mnt/files/setter_tracker.py match kit/ in the repo by md5 (if either differs or is missing, write the repo copy, for example as one base64 xz tar extracted in a cell).
3. In one cell: import datetime as dt, json, time; exec(open('/mnt/files/bali_metrics.py').read()); exec(open('/mnt/files/setter_tracker.py').read()); tracker_start(). Then in later cells call tracker_step() in a loop for at most about 25 seconds per cell, and repeat until a step returns a string ending in "done". Every cell must finish within about 45 seconds; never use background threads. If the workbench restarts (variables gone), re-exec both files without calling tracker_start() and keep calling tracker_step(): it resumes from /mnt/files/tracker_state.pkl. A step that fails with a Close 429 or a connection reset: call tracker_step() again (it repeats the same step).
4. When done, reply with one line: the date and, per setter, how many leads are new, due today and overdue (from tracker_result()).
5. If Composio returns "API key revoked or expired" or another auth error, say in one line that the Composio connector needs to be reconnected in Claude's settings, and stop. If the Google Sheets call fails with a permission error, say the Google Sheets connection in Composio needs reconnecting, and stop.

Writing rules: no em dashes; never say leads "clicked on the site".
```
