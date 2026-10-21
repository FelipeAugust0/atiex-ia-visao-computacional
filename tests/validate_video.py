"""Actual model/video integration report, no webcam or fabricated detections."""
import json
import cv2
from app.vision import Detector,ROOT

def main():
    cap=cv2.VideoCapture(str(ROOT/'assets'/'polichinelos.mp4'))
    detector=Detector('pose');n=0;detected=0;states={};fps=cap.get(cv2.CAP_PROP_FPS) or 30
    try:
        assert cap.isOpened()
        while True:
            ok,frame=cap.read()
            if not ok: break
            n+=1
            if n%3: continue
            scale=min(640/frame.shape[1],480/frame.shape[0])
            frame=cv2.resize(frame,None,fx=scale,fy=scale)
            result=detector.process(frame,round(n*1000/fps))
            detected+=bool(result['points']);states[result['status']]=states.get(result['status'],0)+1
        assert n>0 and detected>0
        print(json.dumps(dict(frames_read=n,frames_detected=detected,repetitions=detector.counter.count,states=states),ensure_ascii=True))
    finally:
        cap.release();detector.close()

if __name__=='__main__':main()
