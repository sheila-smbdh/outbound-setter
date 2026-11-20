# Routine: inbound setter scorecards (Nov 20, 2026, Sheila)

Weekdays at 9:00am ET (`CRON_TZ=America/New_York 0 9 * * 1-5`), a fresh cloud session in this repo's environment builds:

- the inbound cards for Jose, Jordan and Dave, posted only to #setter-sync (`C095GLLCU2U`), and
- Jose's Incomplete Typeform outbound card, posted only to the outbound channel (`C0C9VANP6QN`).

Run problems go to Sheila's own DM (`D0BLE68V517`). Layout and rules: `docs/INBOUND-SCORECARD.md`. The routine was created paused: Sheila turns it on once Messi's price and direct-booking reports are running again.

Trigger id `trig_01AHuok3nMbS23ugAwxef6VF`, created Nov 20, 2026 and paused right away. It was created without connectors or a repo attached (this session couldn't pass them on): add Slack and this repo in the claude.ai Routines settings. Its first run time came back as 9:07am ET.

Connectors the routine needs: **Slack** (read the two Messi channels, post the cards) and **Composio** with Google Sheets (the draw tracker). Close needs no connector: the cloud proxy signs in to api.close.com. The repo `sheila-smbdh/outbound-setter` should be attached. 

Stored prompt, word for word:

```
You are building the daily inbound setter scorecards for Sheila Xu: one inbound card each for Jose, Jordan and Dave, and Jose's Incomplete Typeform outbound card. Post the inbound cards ONLY to the Slack channel C095GLLCU2U (#setter-sync) and Jose's outbound card ONLY to C0C9VANP6QN. Problems with the run itself go ONLY to Sheila's own Slack DM, D0BLE68V517. Never post anywhere else, never DM the setters, never write to Close, and do not commit or edit repo files. The one other write you make is the inbound draw tracker: the tabs "Inbound Days" (columns A to O and R) and "Inbound Weeks" (columns A to I and L) of the Google Sheet "Setter Draw Tracker" (1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE), through Composio. Sheila approved that as a standing write on Nov 20, 2026. Never write Inbound Days P:Q or Inbound Weeks J:K (Sheila's and Jay's overrides), any other tab, or anything else in Drive.

0. If the Slack tools are missing from this session (check with ToolSearch for slack_send_message), stop and say in one line that Sheila needs to add Slack to this routine in the claude.ai Routines settings.
1. Get the repo sheila-smbdh/outbound-setter: if it isn't already in the working directory, attach it with add_repo and clone it as add_repo says. Run git pull origin main, then read CLAUDE.md and docs/INBOUND-SCORECARD.md. If this prompt and the docs disagree, the docs win.
2. The day to cover, D, in America/New_York as YYYY-MM-DD: yesterday, and on Monday the Friday before. WEEK = every weekday from that week's Monday through D.
3. Messi's checks, one file per day d in WEEK, written to flags/<d>.json in the repo folder (not committed):
   {"date": d, "price": {"checked": true|false, "hits": [{"setter": "jose|jordan|dave", "lead": "<lead name>", "time": "<time of the line, e.g. 3:15pm>", "quote": "<exact quote>"}]},
    "booking": {"checked": true|false, "hits": [{"setter": "jose|jordan|dave", "lead": "<lead name>", "closer": "<closer>", "time": "<when booked>"}]}}
   a. Price: read the Slack channel C0C3JB44155 (#ai-call-review-test) with slack_read_channel and slack_read_thread. Messi posts a daily setter price check about 5am ET covering the previous day. hits = every program dollar amount Messi reports for d for Dave (David Martin), Jose (Jose Rodriguez) or Jordan (Jordan Kempster). checked = true only when Messi posted that day's price check: an alert or its all-clear line for d. With nothing from Messi for d, checked = false. Ignore Messi's "Setter Call Script Compliance Report" and dry runs or tests.
   b. Direct-to-closer bookings: read C0C5CGGGE1M (#sales-reports). Messi posts a dated thread ":rotating_light: DIRECT-TO-CLOSER BOOKING ALERTS · <weekday, month day, year>" and replies in it with each direct booking. hits = the replies for d that name Dave, Jose or Jordan as the setter. checked = true when d's thread exists and holds no error or failed-run line from Messi; false when the thread is missing or Messi says a run failed. Silence in an existing thread means no direct bookings (Sheila, Nov 20).
4. Close data, first choice: the Close REST API directly, GET only (Sheila's named exception for this read-only kit; kit/close_direct.py refuses anything but GET). From kit/, each its own command (Bash timeout 600000):
   python3 run_inbound.py <D> jose jordan dave --flags ../flags --out ../d/<D>
   python3 run_direct.py <D> jose_it --out ../d/<D>
   run_direct prints dialed for jose_it; dialed false means Jose made no Incomplete Typeform calls on D: no outbound card and nothing in C0C9VANP6QN about it. Never write to Close and never change close_direct.py. If either fails with HTTP 401 or 403, a 5xx, or a network error (an empty day or a 404 is an answer, not a failure), send one line to D0BLE68V517 saying the direct Close API failed, with the status code, and stop.
5. Draw tracker (Jose and Jordan; draw weeks from Mon Nov 23, 2026). Load COMPOSIO_PROXY_EXECUTE with ToolSearch. Read both tabs with toolkit_slug googlesheets, method GET: endpoint https://sheets.googleapis.com/v4/spreadsheets/1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE/values/'Inbound%20Days'!A1:O3000 saved as draw/days.json, and .../values/'Inbound%20Weeks'!A1:B500 saved as draw/weeks.json (each the response data object with "values"). Then from kit/: python3 inbound_draw.py ../draw/days.json ../draw/weeks.json ../d/<D>/inbound-jose.json ../d/<D>/inbound-jordan.json --out ../draw. Write it with one request: method POST, endpoint https://sheets.googleapis.com/v4/spreadsheets/1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE/values:batchUpdate, body = the exact contents of draw/inbound-draw-sheet.json. If a read fails, skip the write and tell Sheila in D0BLE68V517. If the write fails, check whether the rows already landed (GET as above) before retrying once; if it still fails, tell Sheila and carry on. If Composio returns "API key revoked or expired", tell Sheila to reconnect Composio and carry on with the cards.
6. Render: pip install playwright requests if missing (no playwright install: the browser is at /opt/pw-browsers/chromium and the kit falls back to it). From kit/:
   python3 inbound_build.py ../d/<D>/inbound-<key>.json ../out   (for jose, jordan, dave)
   python3 build.py ../d/<D>/metrics-jose_it.json ../out   (only when jose_it dialed; no --draw)
   Look at each PNG once to check it rendered and that the verdict line matches the table's totals row.
7. Post. To C095GLLCU2U, in order Jose, Jordan, Dave: upload ../out/inbound-<key>-<D>.png with no initial_comment and no other text. To C0C9VANP6QN, only when jose_it dialed: upload ../out/scorecard-jose_it-<D>-0-cover.png the same way. Upload: slack_get_file_upload_url, then curl -sS -X POST <the exact upload URL> -H "Content-Type: image/png" --data-binary @<png>, then slack_complete_file_upload with the channel_id. No summary lines, no thread replies. If an upload is blocked or fails, post nothing more to that channel; send one slack_send_message to D0BLE68V517 saying which card could not be posted and why, then send the PNGs with SendUserFile.
8. If any day in WEEK had price or booking checked = false, add one line to D0BLE68V517 naming the day and the check, so Sheila knows the card shows "not checked".
9. Writing rules: no em dashes, and never say leads "clicked on the site". Keep messages short.
```
