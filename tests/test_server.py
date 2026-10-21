import base64
import time
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.server import app

@pytest.fixture
def client():
    with TestClient(app) as c: yield c

def image(w=320,h=240):
    ok,encoded=cv2.imencode('.jpg',np.zeros((h,w,3),np.uint8))
    assert ok
    return base64.b64encode(encoded).decode()

def test_pages(client):
    for url in ['/','/polichinelos','/numeros','/static/site.js','/static/style.css','/demo.mp4']:
        assert client.get(url).status_code==200

@pytest.mark.parametrize('mode',['pose','hand'])
def test_real_inference_socket(client,mode):
    with client.websocket_connect('/ws/'+mode) as ws:
        assert ws.receive_json()['type']=='ready'
        ws.send_json({'id':1,'image':image()})
        r=ws.receive_json();assert r['id']==1 and r['points']==[]
        assert r['value']==(0 if mode=='pose' else None)
        ws.send_json({'type':'reset'});assert ws.receive_json()['value']==0

@pytest.mark.parametrize('message',[{'id':1,'image':'invalid!'}, {'id':'oops','image':''}, [], {'id':1,'image':image(641,480)}])
def test_invalid_frames(client,message):
    with client.websocket_connect('/ws/pose') as ws:
        assert ws.receive_json()['type']=='ready'
        ws.send_json(message)
        assert ws.receive_json()['type']=='error'

def test_sessions(client):
    with client.websocket_connect('/ws/pose') as a,client.websocket_connect('/ws/pose') as b:
        assert a.receive_json()['type']=='ready';assert b.receive_json()['type']=='ready'
        for ws in [a,b]:
            ws.send_json({'id':1,'image':image()});assert ws.receive_json()['id']==1

def test_large_message(client):
    with client.websocket_connect('/ws/hand') as ws:
        assert ws.receive_json()['type']=='ready'
        ws.send_text('x'*450001);assert ws.receive_json()['type']=='error'

def test_missing_model(client,monkeypatch):
    def missing(mode): raise FileNotFoundError('Modelo ausente: teste')
    monkeypatch.setattr('app.server.Detector',missing)
    with client.websocket_connect('/ws/hand') as ws:
        assert 'Modelo ausente' in ws.receive_json()['message']

def test_cleanup(client,monkeypatch):
    closed=[]
    from app.vision import Detector
    original=Detector.close
    def close(self):
        original(self);closed.append(True)
    monkeypatch.setattr(Detector,'close',close)
    with client.websocket_connect('/ws/pose') as ws:
        assert ws.receive_json()['type']=='ready'
    assert closed==[True]

def test_wrong_origin(client):
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/ws/pose',headers={'origin':'https://example.com'}):pass
