"""Real HTTP/WebSocket round trip against a running local Uvicorn server."""
import asyncio
import base64
import json
import urllib.request
import cv2
import websockets

async def main():
    for path in ['/','/polichinelos','/numeros']:
        with urllib.request.urlopen('http://127.0.0.1:8000'+path) as response:
            assert response.status==200
    cap=cv2.VideoCapture('app/assets/polichinelos.mp4')
    results=0;last=None;n=0
    try:
        async with websockets.connect('ws://127.0.0.1:8000/ws/pose',origin='http://127.0.0.1:8000') as ws:
            assert json.loads(await ws.recv())['type']=='ready'
            while True:
                ok,frame=cap.read()
                if not ok:break
                n+=1
                if n%3:continue
                frame=cv2.resize(frame,(640,360))
                ok,jpeg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,85]);assert ok
                await ws.send(json.dumps({'id':n,'image':base64.b64encode(jpeg).decode()}))
                last=json.loads(await ws.recv())
                assert last['type']=='result' and last['id']==n
                results+=1
                await asyncio.sleep(.085)
            assert last and last['value']>0
            print(json.dumps(dict(results=results,count=last['value'],last_frame_id=last['id'])))
    finally:cap.release()

if __name__=='__main__':asyncio.run(main())
