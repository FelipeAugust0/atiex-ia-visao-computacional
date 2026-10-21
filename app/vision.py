from pathlib import Path
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from .logic import JumpCounter, HandStabilizer, FingerFilter, fingers_up, POSE_EDGES, HAND_EDGES

ROOT=Path(__file__).resolve().parent

class Detector:
    def __init__(self, mode):
        self.mode=mode
        name='pose_landmarker_full.task' if mode=='pose' else 'hand_landmarker.task'
        path=ROOT/'models'/name
        if not path.is_file(): raise FileNotFoundError(f'Modelo ausente: {name}. Execute python -m app.prepare_models antes da feira.')
        base=python.BaseOptions(model_asset_path=str(path))
        if mode=='pose':
            options=vision.PoseLandmarkerOptions(base_options=base,running_mode=vision.RunningMode.VIDEO,min_pose_detection_confidence=.6,min_tracking_confidence=.6)
            self.engine=vision.PoseLandmarker.create_from_options(options)
        else:
            options=vision.HandLandmarkerOptions(base_options=base,running_mode=vision.RunningMode.VIDEO,num_hands=2,min_hand_detection_confidence=.6,min_tracking_confidence=.6)
            self.engine=vision.HandLandmarker.create_from_options(options)
        self.counter=JumpCounter(); self.stable=HandStabilizer(); self.finger_filter=FingerFilter(); self.timestamp=0

    def process(self, frame, timestamp):
        self.timestamp=max(self.timestamp+1,int(timestamp))
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        image=mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
        result=self.engine.detect_for_video(image,self.timestamp)
        if self.mode=='pose':
            points=[[p.x,p.y,p.z,p.visibility] for p in result.pose_landmarks[0]] if result.pose_landmarks else []
            status=self.counter.update(points,frame.shape[1],frame.shape[0])
            return dict(points=points,edges=POSE_EDGES,value=self.counter.count,status=status,phase=self.counter.phase)
        hands=result.hand_landmarks
        points=[[p.x,p.y,p.z] for p in hands[0]] if len(hands)==1 else []
        # Correct for aspect ratio; inferred depth is too noisy for strict
        # straightness tests with a single webcam. UI asks for palm-facing hands.
        planar=[[p[0]*frame.shape[1],p[1]*frame.shape[0],0] for p in points]
        raised=self.finger_filter.update(fingers_up(planar) if planar else None)
        value=self.stable.update(sum(raised) if points else None,self.timestamp)
        status='Mostre apenas uma mão' if len(hands)>1 else 'Nenhuma mão detectada' if not points else 'Estabilizando…' if value is None else 'Número reconhecido'
        return dict(points=points,edges=HAND_EDGES,value=value,status=status,raised=raised)

    def reset(self):
        self.counter=JumpCounter(); self.stable=HandStabilizer(); self.finger_filter=FingerFilter()

    def close(self):
        self.engine.close()
