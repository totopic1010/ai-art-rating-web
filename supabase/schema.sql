-- AI Art Rating: run once in Supabase SQL Editor.
-- The public client never connects directly to these tables.
create table if not exists public.artworks (
 id text primary key,
 title text not null,
 genre text not null
);
create table if not exists public.ratings (
 artwork_id text not null references public.artworks(id),
 participant_id uuid not null,
 score integer not null check(score between 0 and 100),
 reason text not null default '',
 duration_seconds numeric not null check(duration_seconds between 0 and 3600),
 revised_score integer check(revised_score between 0 and 100),
 info_shown boolean not null default false,
 created_at timestamptz not null default now(),
 primary key(artwork_id,participant_id)
);
create table if not exists public.pair_votes (
 participant_id uuid not null,
 left_id text not null references public.artworks(id),
 right_id text not null references public.artworks(id),
 winner_id text not null references public.artworks(id),
 created_at timestamptz not null default now(),
 primary key(participant_id,left_id,right_id),
 check(left_id < right_id),
 check(winner_id in (left_id,right_id))
);
alter table public.artworks enable row level security;
alter table public.ratings enable row level security;
alter table public.pair_votes enable row level security;
revoke all on public.artworks, public.ratings, public.pair_votes from anon, authenticated;
-- Only the backend secret can access tables through the Data API.
insert into public.artworks(id,title,genre) values
('ART-001','光を見上げる人物','人物'),
('ART-002','赤いポピー','その他'),
('ART-003','空中の城','シュルレアリスム'),
('ART-004','青と金の渦','抽象'),
('ART-005','白い猫','その他'),
('ART-006','紅葉の光','風景'),
('ART-007','黄色い百合','その他'),
('ART-008','虹色の結晶','抽象'),
('ART-009','雪山の朝','風景'),
('ART-010','墨と赤の運動','抽象'),
('ART-011','海のクラゲ','その他'),
('ART-012','黄色い回廊','シュルレアリスム'),
('ART-013','絵具と青年','人物'),
('ART-014','桜の枝','風景'),
('ART-015','オーロラの夜','風景'),
('ART-016','大理石の肖像','人物'),
('ART-017','炎の渦','抽象'),
('ART-018','夜の都市','シュルレアリスム'),
('ART-019','水とレモン','その他'),
('ART-020','月下の鹿','シュルレアリスム'),
('ART-021','透明な幾何学','抽象'),
('ART-022','ひまわり','その他'),
('ART-023','夕暮れの浜辺','風景'),
('ART-024','彩色された横顔','人物'),
('ART-025','緑の森の小径','風景'),
('ART-026','黒い墨の軌跡','抽象'),
('ART-027','赤い金魚','その他'),
('ART-028','氷の結晶','抽象'),
('ART-029','星雲の夢','シュルレアリスム'),
('ART-030','白い睡蓮','その他'),
('ART-031','雪の村','風景'),
('ART-032','苺のパフェ','その他'),
('ART-033','雲の海','風景'),
('ART-034','鮮やかな筆致','抽象'),
('ART-035','白馬','その他'),
('ART-036','静かな横顔','人物'),
('ART-037','赤い円の空間','抽象'),
('ART-038','青い花畑','風景'),
('ART-039','ステンドグラス','その他'),
('ART-040','飛翔するフクロウ','その他'),
('ART-041','赤い林檎','その他'),
('ART-042','天空の宮殿','シュルレアリスム'),
('ART-043','墨絵の山水','風景'),
('ART-044','銀河の夜','風景'),
('ART-045','紫水晶','抽象'),
('ART-046','白い花束','その他'),
('ART-047','海辺の夕景','風景'),
('ART-048','赤い花の抽象','抽象'),
('ART-049','水の飛沫','抽象'),
('ART-050','紅い絵具の肖像','人物')
on conflict(id) do update set title=excluded.title,genre=excluded.genre;

-- Returns aggregate-only JSON. This function is accessible only to the server role.
create or replace function public.art_rating_summary()
returns jsonb language sql stable security definer set search_path = public as $$
select jsonb_build_object(
 'count', (select count(*) from ratings),
 'average', (select round(avg(score)::numeric,1) from ratings),
 'artworks', coalesce((
   select jsonb_agg(jsonb_build_object('id',id,'count',n,'average',av) order by id)
   from (select artwork_id id,count(*) n,round(avg(score)::numeric,1) av
         from ratings group by artwork_id) sub
 ), '[]'::jsonb),
 'genres', coalesce((
   select jsonb_agg(jsonb_build_object('genre',genre,'count',n,'average',av) order by genre)
   from (select a.genre,count(*) n,round(avg(r.score)::numeric,1) av
         from ratings r join artworks a on a.id=r.artwork_id group by a.genre) sub
 ), '[]'::jsonb),
 'distribution', (
   select jsonb_build_object('0',count(*) filter(where score between 0 and 19),
    '20',count(*) filter(where score between 20 and 39),
    '40',count(*) filter(where score between 40 and 59),
    '60',count(*) filter(where score between 60 and 79),
    '80',count(*) filter(where score between 80 and 100)) from ratings
 ),
 'reasons', coalesce((select jsonb_object_agg(reason,n) from
    (select reason,count(*) n from ratings where reason<>'' group by reason) t), '{}'::jsonb),
 'avg_duration', (select round(avg(duration_seconds)::numeric,1) from ratings),
 'avg_shift', (select round(avg(revised_score-score)::numeric,1)
               from ratings where revised_score is not null),
 'shift_count', (select count(*) from ratings where revised_score is not null),
 'pair_count', (select count(*) from pair_votes)
);
$$;
revoke all on function public.art_rating_summary() from public, anon, authenticated;
grant execute on function public.art_rating_summary() to service_role;
