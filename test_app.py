import os
import sys
from pathlib import Path
import uuid

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import app as mod


def test_app_flow(tmp_path,monkeypatch):
    monkeypatch.setattr(mod,'DATABASE',tmp_path/'data.sqlite3')
    monkeypatch.setattr(mod,'IS_HOSTED',False)
    monkeypatch.setattr(mod,'HAS_SUPABASE',False)
    client=TestClient(mod.app)
    assert client.get('/').status_code==200
    assert client.get('/api/health').json()['mode']=='local'
    assert len(client.get('/api/artworks').json())==50
    participant=str(uuid.uuid4())
    body={'artwork_id':'ART-001','participant_id':participant,'score':72,'reason':'構図','duration_seconds':12,'revised_score':65,'info_shown':True}
    assert client.post('/api/ratings',json=body).status_code==201
    assert client.post('/api/ratings',json=body).status_code==409
    bad={**body,'score':101,'participant_id':str(uuid.uuid4())}
    assert client.post('/api/ratings',json=bad).status_code==422
    stats=client.get('/api/stats').json()
    assert stats['count']==1
    assert stats['average']==72
    assert stats['shift_count']==1
    assert stats['avg_shift']==-7
    assert stats['distribution']['60']==1
    pair={'participant_id':participant,'left_id':'ART-002','right_id':'ART-003','winner_id':'ART-002'}
    assert client.post('/api/pair',json=pair).status_code==201
    assert client.post('/api/pair',json=pair).status_code==409
    assert client.get('/api/stats').json()['pair_count']==1


def test_hosted_requires_database(monkeypatch):
    monkeypatch.setattr(mod,'IS_HOSTED',True)
    monkeypatch.setattr(mod,'HAS_SUPABASE',False)
    client=TestClient(mod.app)
    assert client.post('/api/ratings',json={'artwork_id':'ART-001','participant_id':str(uuid.uuid4()),'score':50,'duration_seconds':1}).status_code==503
