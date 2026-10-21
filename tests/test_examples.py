import importlib
import cv2
import numpy as np
from app.vagas import ParkingProcessor

def test_imports_do_not_open_capture(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Camera opened during import')
    monkeypatch.setattr(cv2,'VideoCapture',forbidden)
    for name in ['app.contadorPolichinelos','app.vagas','app.escadas']:
        importlib.reload(importlib.import_module(name))

def test_parking_real_frame():
    cap=cv2.VideoCapture('app/assets/video.mp4')
    try:
        ok,frame=cap.read();assert ok
        result=ParkingProcessor().process(frame.copy())
        assert result.shape==frame.shape and np.any(result!=frame)
    finally:cap.release()
