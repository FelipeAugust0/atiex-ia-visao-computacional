"""Terminal entry point; uses exactly the browser inference and counter logic."""
import cv2
if __package__ in (None,''):
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.vision import Detector
from app.cli import run

class PoseProcessor:
    def __init__(self):
        self.detector=Detector('pose')

    def process(self, frame, timestamp):
        result=self.detector.process(frame,timestamp)
        h,w=frame.shape[:2]
        p=result['points']
        for a,b in result['edges']:
            if p and p[a][3]>.6 and p[b][3]>.6:
                cv2.line(frame,(int(p[a][0]*w),int(p[a][1]*h)),(int(p[b][0]*w),int(p[b][1]*h)),(255,255,0),2)
        cv2.putText(frame,f"QTD {result['value']}",(20,60),cv2.FONT_HERSHEY_SIMPLEX,1.4,(255,255,0),3)
        return frame

    def close(self):
        self.detector.close()

def main():
    run(PoseProcessor(),'polichinelos.mp4','Polichinelos')

if __name__=='__main__': main()
