-- GASP agent schema (same tables as livekit-dispatch).
-- Run once in Supabase Dashboard > SQL Editor. Safe to re-run.

drop table if exists events, offers, emergencies, callouts, shifts, caregivers cascade;

create table caregivers (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  phone       text not null unique,
  skills      text[] not null default '{}',
  reliability float not null default 0.9,
  active      boolean not null default true
);

create table shifts (
  id              uuid primary key default gen_random_uuid(),
  client_name     text not null,
  caregiver_id    uuid references caregivers(id),
  starts_at       timestamptz not null,
  ends_at         timestamptz not null,
  required_skills text[] not null default '{}',
  status          text not null default 'scheduled'
);

create table callouts (
  id           uuid primary key default gen_random_uuid(),
  shift_id     uuid not null references shifts(id),
  caregiver_id uuid references caregivers(id),
  reason       text,
  channel      text default 'voice',
  processed    boolean not null default false,
  created_at   timestamptz not null default now()
);

create table offers (
  id           uuid primary key default gen_random_uuid(),
  shift_id     uuid not null references shifts(id),
  caregiver_id uuid not null references caregivers(id),
  wave         int not null default 1,
  channel      text not null default 'sms',
  status       text not null default 'pending',
  sent_at      timestamptz not null default now()
);

create table events (
  id         bigint generated always as identity primary key,
  shift_id   uuid,
  actor      text not null,
  actor_name text,
  action     text not null,
  detail     text,
  created_at timestamptz not null default now()
);

alter publication supabase_realtime add table callouts;

insert into caregivers (name, phone, skills, reliability) values
  ('Maria Lopez', '+15550001', '{dementia,mobility}',   0.95),
  ('James Chen',  '+15550002', '{dementia,wound care}', 0.92),
  ('Aisha Bell',  '+15550003', '{dementia}',            0.81),
  ('Tom Rivera',  '+15550004', '{mobility}',            0.75);

insert into shifts (client_name, caregiver_id, starts_at, ends_at, required_skills)
select 'Mrs. Patterson', id,
       date_trunc('day', now()) + interval '10 hours',
       date_trunc('day', now()) + interval '16 hours',
       '{dementia}'
from caregivers where phone = '+15550001';
