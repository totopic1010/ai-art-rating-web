"""AI Art Rating web application — FastAPI + optional Supabase storage.

Local: SQLite. Hosted (VERCEL=1): requires Supabase, does not silently use ephemeral SQLite.
The browser never receives database secret keys or individual participants' responses.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import os
import sqlite3
import threading
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
PUBLIC = BASE / 'public'
DATA = BASE / 'data'
IS_HOSTED = bool(os.getenv('VERCEL'))
SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY', '')
HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)
DATABASE = DATA / 'ratings.sqlite3'
LOCK = threading.Lock()

app = FastAPI(title='AI Art Rating', version='6.0', docs_url=None, redoc_url=None, openapi_url=None)

with (BASE / 'sample_manifest.csv').open(encoding='utf-8-sig', newline='') as f:
    ARTWORKS = [dict(r) for r in csv.DictReader(f)]
ART_IDS = {art['id'] for art in ARTWORKS}
ART_GENRES = {art['id']: art['genre'] for art in ARTWORKS}


class Rating(BaseModel):
    artwork_id: str = Field(max_length=32)
    participant_id: uuid.UUID
    score: int = Field(ge=0, le=100)
    reason: str = Field(default='', max_length=40)
    duration_seconds: float = Field(ge=0, le=3600)
    revised_score: int | None = Field(default=None, ge=0, le=100)
    info_shown: bool = False


class PairVote(BaseModel):
    participant_id: uuid.UUID
    left_id: str
    right_id: str
    winner_id: str


def local_db():
    DATA.mkdir(exist_ok=True)
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=5000')
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS ratings (
            artwork_id TEXT NOT NULL, participant_id TEXT NOT NULL,
            score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
            reason TEXT NOT NULL, duration_seconds REAL NOT NULL,
            revised_score INTEGER, info_shown INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(artwork_id, participant_id)
        );
        CREATE TABLE IF NOT EXISTS pair_votes (
            participant_id TEXT NOT NULL, left_id TEXT NOT NULL,
            right_id TEXT NOT NULL, winner_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY(participant_id, left_id, right_id)
        );
    ''')
    return conn


def supabase_request(method, route, payload=None, params=None):
    if not HAS_SUPABASE:
        raise HTTPException(503, 'データベース未設定：Supabaseの環境変数を登録してください。')
    headers = {'apikey': SUPABASE_SECRET_KEY, 'Content-Type': 'application/json'}
    if route != 'rpc/art_rating_summary':
        headers['Prefer'] = 'return=minimal'
    try:
        with httpx.Client(timeout=12) as client:
            resp = client.request(method, f'{SUPABASE_URL}/rest/v1/{route}',
                                  headers=headers, json=payload, params=params)
        # Do not return secret-bearing upstream details to users.
        if resp.status_code == 409:
            raise HTTPException(409, 'この作品はすでに評価済みです。')
        if resp.status_code >= 400:
            raise HTTPException(502, 'データ保存先への接続に失敗しました。設定やテーブルを確認してください。')
        return resp.json() if resp.content else None
    except httpx.RequestError:
        raise HTTPException(502, 'データベースへの通信に失敗しました。') from None


def ensure_storage():
    if IS_HOSTED and not HAS_SUPABASE:
        raise HTTPException(503, '公開環境のデータベースが未設定です。')


@app.get('/api/health')
def health():
    return {'ok': True, 'mode': 'supabase' if HAS_SUPABASE else ('unconfigured' if IS_HOSTED else 'local'),
            'artworks': len(ARTWORKS)}


@app.get('/api/artworks')
def artworks():
    return [{'id': a['id'], 'title': a['title'], 'genre': a['genre'],
             'image_url': '/images/' + a['file']} for a in ARTWORKS]


@app.post('/api/ratings', status_code=201)
def add_rating(r: Rating):
    ensure_storage()
    if r.artwork_id not in ART_IDS:
        raise HTTPException(400, '作品IDが不正です。')
    if r.reason not in ('', '色彩', '構図', '独創性', '感情', '技術', 'その他'):
        raise HTTPException(400, '評価理由が不正です。')
    if r.revised_score is not None and not r.info_shown:
        raise HTTPException(400, '制作情報の提示なしに再評価できません。')
    values = dict(artwork_id=r.artwork_id, participant_id=str(r.participant_id),
                  score=r.score, reason=r.reason, duration_seconds=r.duration_seconds,
                  revised_score=r.revised_score, info_shown=r.info_shown,
                  created_at=datetime.now(timezone.utc).isoformat())
    if HAS_SUPABASE:
        supabase_request('POST', 'ratings', payload=values)
    else:
        with LOCK:
            with local_db() as db:
                try:
                    db.execute('''INSERT INTO ratings
                        (artwork_id,participant_id,score,reason,duration_seconds,revised_score,info_shown,created_at)
                        VALUES(:artwork_id,:participant_id,:score,:reason,:duration_seconds,:revised_score,:info_shown,:created_at)''',
                               {**values, 'info_shown': int(r.info_shown)})
                except sqlite3.IntegrityError:
                    raise HTTPException(409, 'この作品はすでに評価済みです。') from None
    return {'saved': True}


@app.post('/api/pair', status_code=201)
def add_pair(p: PairVote):
    ensure_storage()
    if len({p.left_id, p.right_id}) != 2 or p.left_id not in ART_IDS or p.right_id not in ART_IDS:
        raise HTTPException(400, '比較作品が不正です。')
    if p.winner_id not in (p.left_id, p.right_id):
        raise HTTPException(400, '比較結果が不正です。')
    a, b = sorted([p.left_id, p.right_id])
    values = dict(participant_id=str(p.participant_id), left_id=a, right_id=b,
                  winner_id=p.winner_id, created_at=datetime.now(timezone.utc).isoformat())
    if HAS_SUPABASE:
        supabase_request('POST', 'pair_votes', payload=values)
    else:
        with LOCK:
            with local_db() as db:
                try:
                    db.execute('''INSERT INTO pair_votes
                        (participant_id,left_id,right_id,winner_id,created_at)
                        VALUES(:participant_id,:left_id,:right_id,:winner_id,:created_at)''', values)
                except sqlite3.IntegrityError:
                    raise HTTPException(409, 'この組み合わせは比較済みです。') from None
    return {'saved': True}


def aggregate(rows, pairs):
    by_art = defaultdict(list)
    genres = defaultdict(list)
    dist = Counter()
    reasons = Counter()
    durations = []
    shifts = []
    for r in rows:
        score = int(r['score'])
        by_art[r['artwork_id']].append(score)
        genres[ART_GENRES.get(r['artwork_id'], '未分類')].append(score)
        dist[str((score // 20) * 20 if score < 100 else 80)] += 1
        if r['reason']:
            reasons[r['reason']] += 1
        durations.append(float(r['duration_seconds']))
        if r['revised_score'] is not None:
            shifts.append(int(r['revised_score']) - score)
    total = sum(len(x) for x in by_art.values())
    return {'count': total,
            'average': round(sum(sum(v) for v in by_art.values()) / total, 1) if total else None,
            'artworks': [{'id': id_, 'count': len(values), 'average': round(sum(values)/len(values),1)}
                         for id_,values in sorted(by_art.items())],
            'genres': [{'genre': name, 'count': len(values), 'average': round(sum(values)/len(values),1)}
                       for name, values in sorted(genres.items())],
            'distribution': {k:dist.get(k,0) for k in ('0','20','40','60','80')},
            'reasons': dict(reasons),
            'avg_duration': round(sum(durations)/len(durations),1) if durations else None,
            'avg_shift': round(sum(shifts)/len(shifts),1) if shifts else None,
            'shift_count': len(shifts), 'pair_count': len(pairs)}


@app.get('/api/stats')
def stats():
    ensure_storage()
    if HAS_SUPABASE:
        # Aggregation occurs in Postgres; no individual response records are returned.
        result = supabase_request('POST', 'rpc/art_rating_summary', payload={})
        return result
    with LOCK:
        with local_db() as db:
            rows = [dict(r) for r in db.execute('SELECT * FROM ratings')]
            pairs = [dict(r) for r in db.execute('SELECT * FROM pair_votes')]
    return aggregate(rows, pairs)


# Mount static frontend last, so /api paths take precedence.
app.mount('/', StaticFiles(directory=PUBLIC, html=True), name='frontend')
