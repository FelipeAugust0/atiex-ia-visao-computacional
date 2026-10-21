import asyncio
import base64
import json
import logging
import time
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from .vision import Detector, ROOT

app=FastAPI(title='Visão / SENAI')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')

@app.get('/')
@app.get('/polichinelos')
@app.get('/numeros')
def page():
    return FileResponse(ROOT/'static'/'index.html')

@app.get('/demo.mp4')
def demo():
    return FileResponse(ROOT/'assets'/'polichinelos.mp4',media_type='video/mp4')

@app.websocket('/ws/{mode}')
async def socket(ws:WebSocket,mode:str):
    # Same-origin only; no visitor images are persisted.
    origin=ws.headers.get('origin')
    if mode not in ('pose','hand') or (origin and origin.split('://')[-1]!=ws.headers.get('host')):
        await ws.close(code=1008); return
    await ws.accept()
    detector=None
    try:
        detector=await run_in_threadpool(Detector,mode)
        await ws.send_json({'type':'ready'})
        last_id=-1; last_time=0
        while True:
            raw=await asyncio.wait_for(ws.receive_text(),timeout=45)
            if len(raw)>450000: raise ValueError('Quadro excede o limite de 450 KB.')
            data=json.loads(raw)
            if not isinstance(data,dict): raise ValueError('Mensagem inválida.')
            if data.get('type') in ('reset','resume'):
                count=detector.counter.count
                detector.reset()
                if data['type']=='resume': detector.counter.count=count
                await ws.send_json({'type':'reset','value':detector.counter.count}); continue
            fid=data.get('id')
            if type(fid) is not int or fid<0 or fid<=last_id: raise ValueError('Identificador de quadro inválido.')
            if time.monotonic()-last_time<.07: raise ValueError('Envio rápido demais. Limite: 12 quadros/s.')
            encoded=data.get('image')
            if not isinstance(encoded,str): raise ValueError('Imagem inválida.')
            blob=base64.b64decode(encoded,validate=True)
            # Verify JPEG dimensions before allowing OpenCV to allocate decoded pixels.
            from PIL import Image
            from io import BytesIO
            with Image.open(BytesIO(blob)) as header:
                if header.format!='JPEG' or header.width>640 or header.height>480: raise ValueError('Use JPEG até 640 × 480.')
            frame=cv2.imdecode(np.frombuffer(blob,np.uint8),cv2.IMREAD_COLOR)
            if frame is None: raise ValueError('Não foi possível ler a imagem.')
            last_id=fid; last_time=time.monotonic()
            result=await run_in_threadpool(detector.process,frame,int(time.monotonic()*1000))
            await ws.send_json(dict(type='result',id=fid,**result))
    except WebSocketDisconnect:
        pass
    except (ValueError,KeyError,TypeError,FileNotFoundError,asyncio.TimeoutError) as exc:
        try: await ws.send_json({'type':'error','message':str(exc) or 'Conexão inativa. Inicie novamente.'})
        except (RuntimeError,WebSocketDisconnect): pass
    except Exception:
        logging.exception('Falha no detector')
        try: await ws.send_json({'type':'error','message':'Não foi possível iniciar ou processar o modelo. Confira a instalação e reinicie a experiência.'})
        except (RuntimeError,WebSocketDisconnect): pass
    finally:
        if detector: await run_in_threadpool(detector.close)
        try: await ws.close()
        except RuntimeError: pass
