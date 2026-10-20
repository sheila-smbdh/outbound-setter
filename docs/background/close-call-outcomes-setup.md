# Close setup for the sales manager (about 15 minutes)

This needs someone with Close's **Manage Customizations** permission (for outcomes) and **Manage Team Phone Numbers** (for the phone number). Close's help docs say call outcomes and voicemail drop come with the Growth and Scale plans.

## 1. Call outcomes (replaces Bali's note codes)

Right now there are no call outcomes in Close. Outcomes live inside a Playbook.

1. Go to **Settings > Playbooks and Outcomes**.
2. Create a Playbook called **Welcome Series Calls**.
3. Add these 8 outcomes. Set each to apply to **calls**, and paste in the description. Close uses the descriptions to fill in outcomes automatically from recorded calls, so they matter.

| Outcome | Description |
|---|---|
| Conversation: set to closer | Talked with the lead and booked a closer call while they were on the phone. |
| Conversation: set to self | Talked with the lead and booked a follow-up on the setter's own calendar. |
| Conversation: not a fit | Talked with the lead; not qualified or not interested. |
| Conversation: call back later | Talked with the lead; they asked to talk another time. |
| Left voicemail | Reached voicemail and left a message. |
| Call screener: got through | An automated call screener answered and the lead then picked up. |
| Call screener: didn't get through | An automated call screener answered and the lead never picked up. |
| No answer / hung up | No answer, no voicemail left, or the lead hung up right away. |

4. Go to **Settings > Communications > Outcomes** and mark **Left voicemail** as the **Voicemail Drop Outcome**. Every dropped voicemail will then log itself.
5. Tell Bali: apply the Welcome Series Calls Playbook on each call (Close may pre-fill it), and pick the outcome during or right after the call. If he misses one, he can add it later from the call's **More** menu.

Note: Close says the outcome picker shows up only on connected calls. A voicemail usually counts as connected, but if Bali can't set an outcome on a voicemail, voicemail drop (step 4) still logs it.

## 2. Bali's US phone number

1. **Settings > Communication > Phone & Voicemail > New Number**: search by a US area code and add the number (it has a monthly cost).
2. Add Bali as a member of the number.
3. Email **support@close.com** and ask them to make it Bali's **primary number**. Close uses the primary number as his default caller ID *and* as the sender for Workflow SMS steps. Only Support can change it.
4. Check the next day: the daily scorecard's "US caller ID" check should read *Done*.

## 3. Voicemail drop for Bali

**Settings > Communication > Phone & Voicemail > Voicemail Drop**: Bali records the SOP section 6 voicemail (under 25 seconds).

Sources: Close help center articles on Outcomes, Using Playbooks on calls, Outbound caller ID, Setting up calling, and Calling (voicemail drop).
