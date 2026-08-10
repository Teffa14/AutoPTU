-- AutoPTU Career 0.1: private authoritative state and minimal public projections.
create extension if not exists pgcrypto with schema extensions;
create extension if not exists pgmq;
create schema if not exists private;

revoke all on schema private from public, anon, authenticated;
grant usage on schema private to service_role;

-- Supabase Queues / PGMQ is the durable transport; battle_results is the audit ledger.
select pgmq.create('career_battle_jobs');

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  handle text not null,
  locale text not null default 'es' check (locale in ('es', 'en')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_handle_format check (handle ~ '^[A-Za-z0-9_-]{3,24}$')
);
create unique index profiles_handle_lower_idx on public.profiles (lower(handle));

create table public.daily_challenges (
  id uuid primary key default gen_random_uuid(),
  challenge_date date not null unique,
  region text not null,
  seed bigint not null,
  catalog jsonb not null,
  rules_version text not null,
  content_version text not null,
  scoring_version text not null,
  published_at timestamptz not null default now()
);

create table private.content_versions (
  id uuid primary key default gen_random_uuid(),
  kind text not null check (kind in ('rules', 'content', 'scoring', 'narrative', 'model')),
  version text not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (kind, version)
);

create table private.career_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  mode text not null check (mode in ('simple', 'advanced')),
  ranked boolean not null default false,
  challenge_id uuid references public.daily_challenges(id),
  seed bigint not null,
  revision bigint not null default 0 check (revision >= 0),
  status text not null default 'active' check (status in ('active', 'retired', 'disqualified')),
  state jsonb not null,
  score bigint not null default 0,
  rules_version text not null,
  content_version text not null,
  scoring_version text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index career_runs_user_created_idx on private.career_runs (user_id, created_at desc);
create index career_runs_active_idx on private.career_runs (user_id, updated_at desc) where status = 'active';
create index career_runs_challenge_idx on private.career_runs (challenge_id, mode, score desc) where ranked;

create table private.run_commands (
  id bigint generated always as identity primary key,
  run_id uuid not null references private.career_runs(id) on delete cascade,
  idempotency_key text not null,
  expected_revision bigint not null,
  command_type text not null,
  payload jsonb not null,
  response jsonb,
  created_at timestamptz not null default now(),
  unique (run_id, idempotency_key)
);
create index run_commands_run_idx on private.run_commands (run_id, id);

create table private.season_snapshots (
  id bigint generated always as identity primary key,
  run_id uuid not null references private.career_runs(id) on delete cascade,
  season_number smallint not null check (season_number > 0),
  revision bigint not null,
  snapshot jsonb not null,
  created_at timestamptz not null default now(),
  unique (run_id, season_number, revision)
);
create index season_snapshots_run_idx on private.season_snapshots (run_id, season_number desc);

create table private.battle_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references private.career_runs(id) on delete cascade,
  battle_key text not null,
  spec jsonb not null,
  result jsonb,
  transcript_sha256 text check (transcript_sha256 is null or transcript_sha256 ~ '^[0-9a-f]{64}$'),
  rules_version text not null,
  status text not null default 'queued' check (status in ('queued', 'running', 'complete', 'failed')),
  retry_count smallint not null default 0 check (retry_count between 0 and 10),
  replay_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (run_id, battle_key)
);
create index battle_results_run_idx on private.battle_results (run_id, created_at);
create index battle_results_queue_idx on private.battle_results (created_at) where status in ('queued', 'failed');

create table private.daily_attempts (
  id bigint generated always as identity primary key,
  challenge_id uuid not null references public.daily_challenges(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  mode text not null check (mode in ('simple', 'advanced')),
  attempt_no smallint not null check (attempt_no between 1 and 3),
  run_id uuid not null unique references private.career_runs(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (challenge_id, user_id, mode, attempt_no)
);
create index daily_attempts_user_idx on private.daily_attempts (user_id, challenge_id, mode);

create table private.competitive_results (
  run_id uuid primary key references private.career_runs(id) on delete cascade,
  challenge_id uuid not null references public.daily_challenges(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  mode text not null check (mode in ('simple', 'advanced')),
  attempt_no smallint not null check (attempt_no between 1 and 3),
  score bigint not null,
  achievements jsonb not null default '[]'::jsonb,
  transcript_root_sha256 text not null check (transcript_root_sha256 ~ '^[0-9a-f]{64}$'),
  verified_at timestamptz not null default now(),
  unique (challenge_id, user_id, mode, attempt_no)
);
create index competitive_results_rank_idx on private.competitive_results (challenge_id, mode, score desc, verified_at);

create table public.leaderboard_entries (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  challenge_id uuid not null references public.daily_challenges(id) on delete cascade,
  mode text not null check (mode in ('simple', 'advanced')),
  handle text not null,
  score bigint not null,
  achievements jsonb not null default '[]'::jsonb,
  completed_at timestamptz not null,
  unique (challenge_id, owner_id, mode)
);
create index leaderboard_entries_rank_idx on public.leaderboard_entries (challenge_id, mode, score desc, completed_at, id);

create table public.career_shares (
  id uuid primary key default gen_random_uuid(),
  share_slug text not null unique check (share_slug ~ '^[a-z0-9_-]{12,64}$'),
  owner_id uuid not null references auth.users(id) on delete cascade,
  summary jsonb not null,
  replay_path text,
  created_at timestamptz not null default now(),
  revoked_at timestamptz
);
create index career_shares_owner_idx on public.career_shares (owner_id, created_at desc);
create index career_shares_live_idx on public.career_shares (share_slug) where revoked_at is null;

alter table public.profiles enable row level security;
alter table public.daily_challenges enable row level security;
alter table public.leaderboard_entries enable row level security;
alter table public.career_shares enable row level security;

create policy profiles_read_own on public.profiles for select to authenticated
  using ((select auth.uid()) = id);
create policy profiles_insert_own on public.profiles for insert to authenticated
  with check ((select auth.uid()) = id);
create policy profiles_update_own on public.profiles for update to authenticated
  using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy daily_challenges_public_read on public.daily_challenges for select to anon, authenticated
  using (true);
create policy leaderboard_public_read on public.leaderboard_entries for select to anon, authenticated
  using (true);
create policy career_shares_public_read on public.career_shares for select to anon, authenticated
  using (revoked_at is null);

revoke all on public.profiles, public.daily_challenges, public.leaderboard_entries, public.career_shares from anon, authenticated;
grant select, insert, update on public.profiles to authenticated;
grant select on public.daily_challenges to anon, authenticated;
grant select (id, challenge_id, mode, handle, score, achievements, completed_at)
  on public.leaderboard_entries to anon, authenticated;
grant select (id, share_slug, summary, replay_path, created_at)
  on public.career_shares to anon, authenticated;

create or replace function private.reserve_daily_attempt(
  requested_challenge uuid,
  requested_user uuid,
  requested_mode text,
  requested_run uuid
) returns smallint
language plpgsql
security definer
set search_path = ''
as $$
declare
  next_attempt smallint;
begin
  if requested_mode not in ('simple', 'advanced') then
    raise exception using errcode = '22023', message = 'invalid career mode';
  end if;
  perform pg_catalog.pg_advisory_xact_lock(
    pg_catalog.hashtextextended(requested_challenge::text || ':' || requested_user::text || ':' || requested_mode, 0)
  );
  select (count(*) + 1)::smallint into next_attempt
  from private.daily_attempts
  where challenge_id = requested_challenge and user_id = requested_user and mode = requested_mode;
  if next_attempt > 3 then
    raise exception using errcode = 'P0001', message = 'daily attempt quota exhausted';
  end if;
  insert into private.daily_attempts (challenge_id, user_id, mode, attempt_no, run_id)
  values (requested_challenge, requested_user, requested_mode, next_attempt, requested_run);
  return next_attempt;
end;
$$;
revoke all on function private.reserve_daily_attempt(uuid, uuid, text, uuid) from public, anon, authenticated;
grant execute on function private.reserve_daily_attempt(uuid, uuid, text, uuid) to service_role;

create or replace function private.claim_battle_job(worker_name text)
returns setof private.battle_results
language sql
security definer
set search_path = ''
as $$
  update private.battle_results
  set status = 'running', updated_at = now()
  where id = (
    select id from private.battle_results
    where status in ('queued', 'failed') and retry_count < 10
    order by created_at
    limit 1
    for update skip locked
  )
  returning *;
$$;
revoke all on function private.claim_battle_job(text) from public, anon, authenticated;
grant execute on function private.claim_battle_job(text) to service_role;

-- Shared replay files are written only by the backend; public reads require an explicit share.
insert into storage.buckets (id, name, public, file_size_limit)
values ('career-shares', 'career-shares', true, 52428800)
on conflict (id) do update set public = excluded.public, file_size_limit = excluded.file_size_limit;

drop policy if exists career_shared_replays_read on storage.objects;
create policy career_shared_replays_read on storage.objects for select to anon, authenticated
  using (bucket_id = 'career-shares');
