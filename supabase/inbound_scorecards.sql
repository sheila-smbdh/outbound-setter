-- Inbound setter scorecards: Supabase tables in setter-data (suoblmuvrmyfmuvlhqce). Sheila, Nov 23, 2026.
-- Run once in the Supabase SQL editor (Claude's Supabase access can't create tables). Safe to run again.
-- The inbound scorecards routine upserts into these tables every run (standing approval, Sheila, Nov 23, 2026).

create table if not exists public.inbound_sc_runs (
  run_id text primary key,             -- e.g. 2026-11-24T09:07 ET
  card_day date not null,              -- the day the cards cover
  status text,                         -- ok | partial | failed
  summary jsonb,                       -- per setter: sets, verdict, booked/scheduled/live, what was posted
  created_at timestamptz default now()
);

create table if not exists public.inbound_sc_days (    -- one row per setter per weekday (Jose, Jordan, Dave)
  day date not null,
  setter text not null,                -- jose | jordan | dave
  intro_calls int, inbound_sets int, inbound_sets_week int,
  booked_calls int, scheduled_calls int, live_calls int,
  steps_due int, steps_done int,
  handoff text, price text, booking text,              -- Met | Missed | None due | Not checked
  verdict text,                        -- Compliant | Not compliant | Not checked
  why text,
  price_hits jsonb, booking_hits jsonb, missed_steps jsonb,
  outbound_sets_total int, outbound_closes_total int,  -- Jose and Jordan, since Oct 20
  draw boolean,                        -- Jose and Jordan: counts toward the weekly draw
  last_run_id text, updated_at timestamptz default now(),
  primary key (day, setter)
);

create table if not exists public.inbound_sc_sets (    -- one row per inbound set
  setter text not null, lead_id text not null, set_day date not null,
  lead_name text, closer text, set_at timestamptz, call_at timestamptz,
  email text, note text, day_before text, day_of text, -- ok | miss | later | ok_prev | miss_prev | na
  price text, booking text,
  last_run_id text, updated_at timestamptz default now(),
  primary key (setter, lead_id, set_day)
);

create table if not exists public.inbound_sc_calls (   -- one row per lead per day on the setter's calendar
  day date not null, setter text not null, lead_id text not null,
  lead_name text, starts_at text,
  booked boolean, scheduled boolean, live boolean, removed_reason text,
  last_run_id text, updated_at timestamptz default now(),
  primary key (day, setter, lead_id)
);

create table if not exists public.outbound_sc_days (   -- Jose's Incomplete Typeform outbound card
  day date not null, setter text not null,             -- jose_it
  dials int, leads_dialed int, speed_pct int, pickup_pct int, connect_pct int,
  vm_pct int, text_pct int, dd_pct int, handoff_due int, handoff_done int,
  sets_to_closer int, sets_since_start int, closes_since_start int,
  metrics jsonb,                       -- the full metrics file
  last_run_id text, updated_at timestamptz default now(),
  primary key (day, setter)
);

create table if not exists public.inbound_sc_feedback (  -- setters' replies on the card threads, and Sheila's or Jay's decision
  reply_ts text primary key,           -- the setter's reply
  channel text, thread_ts text,        -- the card's message
  card_day date, setter text, raised_by text, raised_at timestamptz,
  claim text,                          -- what the setter said, short
  decision text,                       -- pending | approved | rejected
  decided_by text, decision_ts text, decision_text text,
  change_summary text,                 -- what the routine changed
  rule_added text,                     -- the rule written to docs/INBOUND-SCORECARD.md, if any
  commit_sha text, days_rerun jsonb,
  last_run_id text, updated_at timestamptz default now()
);
