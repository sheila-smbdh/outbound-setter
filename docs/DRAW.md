# Setter draw: Jose and Jordan, Nov 16 to Nov 29, 2026 (runbook)

Owner: Sheila Xu. Set Nov 16, 2026.

## The rule

- Jose and Jordan are each **eligible for the draw** for a week when they hit all three KPIs on **5 of its 7 days** ("qualifying days"). In November the draw is $1,000 a week (part of a $2,000 monthly draw, with two weeks left). The card and the sheet never show the amount, only "the draw" (Sheila, Nov 16), because December isn't decided.
- Weeks run Monday to Sunday: **Nov 16 to 22** and **Nov 23 to 29**. The draw ends Nov 30. The Monday Nov 30 run judges Fri Nov 27 to Sun Nov 29 and closes week 2.
- A day is compliant when all three draw KPIs are met:
  1. **Leads dialed:** at least **60 leads** that day. This counts people dialed, not dials, and it is the same number as the card's Leads dialed tile.
  2. **Speed to lead:** at least **60%** of the new sign-ups during their work hours called within **20 minutes**. This uses the same sign-ups and work hours as the card's speed tile, which moved from 15 to 20 minutes on Nov 16.
     - **Team meetings are left out (Sheila, Nov 16).** Sign-ups that arrive during a scheduled team meeting or training don't count either way. The tile's small print says how many were left out.
     - The schedule lives in `MEETINGS_ON` and `MEETINGS_WEEKLY` in `kit/bali_cover.py`:
       - Mon Nov 16: 11:00 to 12:30 ET (team meeting, then training)
       - Tue Nov 17 to Thu Nov 19: 12:00 to 12:30 ET (training)
       - from Mon Nov 23: Mondays 11:00 to 12:00 ET (team meeting only)
     - Update those two lists when the schedule changes.
     - The setters' own inbound calls are not left out (Sheila, Nov 16): they are hard to predict, and 60% is lenient once meetings are out.
     - Checked on the week of Nov 9 to 13 in #outbound-notif:
       - Jose had 28 sign-ups a day in his hours, and Jordan 24.
       - Meetings plus inbound calls would have made 6% (Jose) and 11% (Jordan) impossible to reach within 20 minutes.
  3. **Handoff:** **100%** of the handoff steps due that day were done. These are the four steps on the card's show rate tile:
     - the handoff email within an hour of booking
     - the closer note in Close
     - the day-before reminder, owed when the call was booked 2 or more days out
     - the morning-of reminder, owed unless the lead replied since the setter's last message or accepted the calendar invite. An accepted invite is an incoming email on the lead whose subject starts "Accepted:", Google Calendar's reply to the closer (Sheila, Nov 16). It must arrive after the booking and before the call day.
- **Nothing owed counts as met** (Sheila, Nov 16). This covers a day with no new sign-ups during their hours, or no handoff steps due. Leads dialed always applies.
- **No outbound calls:** the day is not met.
- **Weekends:** setters aren't expected to work weekends. They can work a weekend day to make up a missed weekday (Sheila, Nov 16).
  - A weekend day where they dialed is judged like any other day and gets a card.
  - A weekend day with no outbound calls gets no card and no row in the sheet.
- **Days off (Sheila, Nov 16):** a setter with no outbound calls on a day gets no card and no "no calls" line in the channel. A weekday with no calls still gets a "Not met" row in the sheet. Jordan is out Nov 16 to 18, so expect no Jordan cards those days.

## Where it shows

- **Card layout (Sheila, Nov 16):** top to bottom:
  1. The title.
  2. The line under it: dials, leads, time on the phone, and first to last call.
  3. Two big numbers: sets to a closer and closes since the setter started. Wins and fixes are gone.
  4. The draw box. Its wording (Sheila, Nov 16) is built on the term "qualifying day", meaning a day with all 3 KPIs hit. It holds:
     - the rule line: "The draw: hit all 3 KPIs on 5 of the 7 days this week (Mon to Sun) to be eligible."
     - "Today is (not) a qualifying day", with the week count ("1 of 5 qualifying days this week")
     - the three KPI boxes and a chip per day
     - the week status: "Need N more qualifying days by Sun, Nov 22 to be eligible.", "Eligible for this week's draw." or "Not eligible this week: ..."
  5. "Draw KPIs: hit all 3 for a qualifying day": speed to lead and leads dialed stacked on the left, the handoff tile on the right.
  6. "Other numbers", smaller, 3 and 3: pickup, connect, set to a closer; voicemail, text, double dial.
- **Handoff tile:** it replaces the show rate tile. Its big number is the day's handoff steps done (for example "3 of 4 done"), with a target of 100%. Under it is one row per step with who was missed, then the target bar ("Target 100%"). Below a gray line, show rate for the last 7 days sits under "Tracked, no target".
- **The draw box** (`kit/build.py`, `kit/cover.html`) is red or green and shows on Jose's and Jordan's cards Nov 16 to 29 only. The full reason for each miss is in the sheet's "Why not met" column, not on the card.
- During the draw, the speed and leads tiles are red when missed, never yellow "almost".
- Leads dialed is a scored tile with a target of 60.
- **The tracker sheet** "Setter Draw Tracker" (Google Sheet `1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE`, https://docs.google.com/spreadsheets/d/1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE/edit, Sheila's Drive):
  - **Days:** one row per setter per day: the three KPIs, the missed handoff steps by lead, the verdict and why.
    - Column R ("Sheila's override") is Sheila's: type Met or Not met to overrule a day. The routine never writes R.
    - Column S ("Counts as") is the override if set, else the verdict. Weeks counts S.
  - **Weeks:** per setter per week: days met, and eligible for the draw or not. These are formulas, so they update when Days or an override changes.
  - **How it works:** the rules above in short.

## Files

| File | What it does |
|---|---|
| `kit/setter_draw.py` | The draw rules (`draw_day`) and the sheet merge. `python3 setter_draw.py merge <days.json> <metrics files...> --out <dir>` writes `draw-sheet.json` (the Sheets `values:batchUpdate` body for `Days!A:Q` and `Days!S`) and `draw-week-<key>-<date>.json` per card |
| `kit/build.py` | `--draw draw-week-<key>-<date>.json` adds the week to the card's draw box. Without it the box shows the day only |
| `kit/bali_cover.py`, `kit/bali_show.py` | `SETTERS[...]['speed_min'] = 20` for Jose and Jordan. Metrics gain `speed_min` and `within_min`; `within15` is unchanged |

## How the routine runs it

See `prompts/setter-scorecards-routine.md`. In short:

1. Days to cover: yesterday on Tuesday to Friday; Friday, Saturday and Sunday on Monday.
2. Close pull per setter per day: `run_direct.py`, read only.
3. Read the sheet's Days tab with Composio (`googlesheets`, GET `values/Days!A1:S`).
4. Run `setter_draw.py merge`, render each card with `--draw`, and write the Days tab back (A:Q and S only).
5. Post the cards.

Rows are upserted by date and setter, so a rerun of a day replaces its row in place and keeps Sheila's override. Old rows are not recomputed when Close changes later. Rerun a day by hand if a number needs correcting.

Known limit: a handoff step due on a weekend (for example a day-before reminder for a Monday call) is judged only if the setter dialed that weekend day. With no weekend card, the miss shows on no draw day.
