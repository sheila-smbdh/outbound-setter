# Call recordings test: Oct 5, 2026 (run Oct 6)

> Copied verbatim from the claude.ai Project doc `claude/bali-kit/RECORDINGS-TEST-2026-10-05.md` on Oct 20, 2026.

Supersedes the RUNBOOK "Known limits" lines saying recordings can't be checked from here.

## Standing practice (Sheila, Oct 7)

- When asked about a specific lead or call, or when a count looks off (a short call tagged as a conversation, a closer call he didn't post in Slack, a booking that lands minutes after a short call), pull the call recording and transcribe it before answering. Don't explain a call from Close fields alone.

## What works

- Close has no transcripts for our calls (`recording_transcript` and the MCP `transcript` are null: Close's own call transcription is not on). The audio is there: 82 of Bali's 87 Oct 5 calls have a `recording_url`.
- The MP3 downloads through the Composio `close` toolkit. `proxy_execute` returns `{}` for binary, so call the raw endpoint the helper wraps: POST `$BACKEND_URL/api/v3/tool_router/internal/proxy_execute` with `{"toolkit_slug":"close","endpoint":<recording_url>,"method":"GET"}` and header `x-session-access-key: $COMPOSIO_WORKBENCH_ACCESS_KEY`. The reply has `binary_data.url` (signed link, 1 hour), which the workbench can fetch.
- Transcribe in the workbench: `pip install faster-whisper`, model `base.en` int8, cache in `/home/user/whisper` (not `/mnt/files`, I/O error). Decode with ffmpeg in 30-second slices and run one process per recording: the workbench has 1 CPU and about 1 GB RAM and kills larger jobs. Speed is about 0.15x real time (110 min of audio took about 20 min).
- Oct 7 notes: run `pip install` in the background (`nohup ... &`), a foreground install plus transcription crashed the workbench. faster-whisper's own file decoder fails with the workbench's `av` version (`metadata_errors` TypeError); decode with ffmpeg to raw 16 kHz float32 and pass the numpy array to `transcribe()`. Run the transcription as a background process and poll for a done file.
- The Claude container can't fetch the audio itself (egress proxy blocks the signed storage host and huggingface.co).

## Decisions (Sheila, Oct 6)

- **Matt Weiss is not Bali's set.** Matt booked with a closer (Solomon House) himself; on Bali's 33-sec call he says he had just scheduled it, and the meeting was created the same minute. Corrected Oct 5 closer calls = 3 (Leo Franques, Scott Aschermann, Mike Mosel). The closer-call rule in the RUNBOOK still credits Bali in this situation (meeting created within 24 h of his pickup); not yet changed in `bali_metrics.py`.
- **Real conversation (connect) = meaningful outcome or meaningful exchange.** Short calls with little info exchange that only end in "I'll send you an email" are pickups, not connects, even when tagged call back later. A call that leads to a DQ, a self-set (booked) or a closer call counts. Applied to Oct 5: Jaskaran Singh Sarao, Kumar Adipudi, Lily Xa and Michael B Adjepong-Akosah = pickups only. David Erez (67 sec, DQ) = connect.

## Decision (Sheila, Oct 7): Dan Housley, Oct 6

- Bali's 4:21pm ET call (`acti_gQlsB3OBMoVadAdrt8kwEsrma8qlnIccdEjsxJMGlNm`, 51 sec, tagged "Conversation: set to closer") never reached Dan. Recording: a call screener asks for name and reason, Bali says "Hey, Bali", the screener comes back with "this person is not available" and a voicemail prompt. Sheila listened too. Dan most likely booked Nick Vaughan himself (meeting created 4:22pm for Fri Oct 9, 10am ET). Not a pickup, not a connect, not a closer call.
- Corrected Oct 6: pickups 26 of 91 (29%), connect 16 of 91 (18%, unchanged: the 51-sec call was already under the 60-sec floor), set to a closer 2 (Robert Beaton, Veeranjaneyulu Somaraju). Dan joins the first-call no-pickup group: voicemail 51 of 57 (89%), text 48 of 65 (74%, now red). Cover: 2 of 7 targets, 3 almost.
- The Oct 6 scorecard page was republished Oct 7 with these numbers. The saved record `daily/2026-10-06.json` and the PNGs sent the morning of Oct 7 still show the as-sent numbers (pickups 27, closer calls 3).
- Code not changed yet: `bali_metrics.py` still trusts the Close tag. The weekly report for Oct 5 to 9 must treat this call as a screener (not a pickup) and drop Dan from closer calls. Same pattern as Matt Weiss: both were short calls (33 and 51 sec) followed within minutes by a closer meeting the lead booked. Proposed to Sheila: count a closer call only when it follows a real conversation (60+ sec tagged or 3+ min untagged), which would have removed both automatically.

## Oct 5 results (58 people dialed)

| | Scorecard (Close rules) | From the recordings, Sheila's rule |
|---|---|---|
| Pickup rate | 24 of 58 (41%) | 28 of 58 (48%) heard on audio, 29 (50%) with Allen Webb (6 sec, no recording, note "hung on me") |
| Connect rate | 12 of 58 (21%) | 11 of 58 (19%) |
| Closer calls | 3 on the card (4 after the Mike Mosel fix) | 3 (Matt Weiss removed) |

Connects (11):
- Closer call: Leo Franques 9.5 min, Scott Aschermann 12 min, Mike Mosel 9 min.
- Self-set (booked): Thomas Symington 2.5 min, Himanshu Jain 2 min.
- DQ: David Erez 67 sec.
- Long exchange, no booking: Jasen Knight 17 min, Scott Norton 6 min, Shaleen Sharma 5 min, TJ Joseph 5 min, Gaurav Kasar 2.5 min (discussed the $20k fee; the shortest no-booking call counted, confirm with Sheila if in doubt).

Scorecard vs recordings: the card counted Jaskaran and Michael (tagged call back later, 60+ sec) and missed Gaurav (untagged, under 3 min). Net 12 to 11.

Pickups missed by the rules: Rich Tway (tagged "No answer / hung up", 39 sec talk), Dwaine Lucas 41s, Shwet Raddi 43s, Wilson Rodrigues 32s, Thomas Sanchez 29s (confirmation call), all untagged under 45 sec. Wrongly counted: Carl Cole (47 sec untagged, Bali left a voicemail).

Other finds:
- David Erez's DQ note says low liquidity, but liquidity never came up on the recorded call (language barrier).
- Dilip Kampa and Thomas Sanchez calls are logistics on meetings already booked, not new conversations.
- Short-call brush-offs (busy, call me back, send a link) under 60 sec: Abner Fearon, Dwaine Lucas, Frank Benevento, Habtom Desu, Rohit Sharma, Shwet Raddi, Vinay Tandel, Wilson Rodrigues, Rich Tway.

The scorecard code and saved Oct 5 record are unchanged.
