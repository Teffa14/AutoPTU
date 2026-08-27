create or replace function private.project_leaderboard_trainer_name()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  projected_name text;
begin
  select nullif(pg_catalog.btrim(cr.state #>> '{build,name}'), '')
    into projected_name
  from private.competitive_results r
  join private.career_runs cr on cr.id = r.run_id
  where r.challenge_id = new.challenge_id
    and r.user_id = new.owner_id
    and r.mode = new.mode
    and r.score = new.score
  order by r.verified_at asc, r.run_id asc
  limit 1;

  if projected_name is not null then
    new.handle := projected_name;
  end if;
  return new;
end;
$$;

revoke all on function private.project_leaderboard_trainer_name() from public, anon, authenticated;
grant execute on function private.project_leaderboard_trainer_name() to service_role;

drop trigger if exists leaderboard_trainer_name_projection on public.leaderboard_entries;
create trigger leaderboard_trainer_name_projection
before insert or update of score on public.leaderboard_entries
for each row execute function private.project_leaderboard_trainer_name();

with projected as (
  select distinct on (r.challenge_id, r.user_id, r.mode, r.score)
    r.challenge_id,
    r.user_id,
    r.mode,
    r.score,
    nullif(pg_catalog.btrim(cr.state #>> '{build,name}'), '') as trainer_name
  from private.competitive_results r
  join private.career_runs cr on cr.id = r.run_id
  order by r.challenge_id, r.user_id, r.mode, r.score, r.verified_at asc, r.run_id asc
)
update public.leaderboard_entries e
set handle = projected.trainer_name
from projected
where projected.challenge_id = e.challenge_id
  and projected.user_id = e.owner_id
  and projected.mode = e.mode
  and projected.score = e.score
  and projected.trainer_name is not null;
