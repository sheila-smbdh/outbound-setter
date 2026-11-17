# Outbound sets, weekly, scorecard set rule (Sheila, Nov 17, 2026)

Bali, Jose and Jordan only. Weeks run Sunday to Saturday, Aug 16 to Nov 14, 2026. Close as of Nov 17, 2026, read only.

- **A set** is what the daily scorecards count as a closer call: `_bookings` in `kit/bali_metrics.py` (real pickup, answered callback, Zoom the lead joined, or a text or email handoff within 14 days; no earlier meeting with the same person before the setter's first real call; no other rep's call in between). Closer meetings later canceled are not sets, as on a card rerun today. Closers: the cards' 13 plus Ezra Isla, Chris Cha and Kameron Bryant (no sets to those three).
- **Outbound:** the setter's Pre-Discovery form type; with no type, inbound when the lead had an intro meeting on the setter's calendar in the 3 days before, otherwise outbound (Setter Sets rule, `docs/SETTER-SETS.md`). 13 card sets are typed inbound and left out.
- **Result:** the closer bucket from `docs/SETTER-SETS.md`, where the lead is today. Percentages are out of showed sets. Closed = Won. Warm = next 7 days, in month closing. Long term cold = farm and no timeline. Last column = bad fit, offer not presented, lost for another reason.
- `leads.csv`: one row per set. `weekly.csv`: the table.
