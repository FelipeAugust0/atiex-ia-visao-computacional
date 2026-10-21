"""Optional real-model check using the image from Google's official notebook.

Download explicitly into .artifacts/hand-reference.jpg; never downloads at runtime.
"""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from app.vision import Detector, ROOT

def main():
    image=cv2.imread(str(ROOT.parent/'.artifacts'/'hand-reference.jpg'))
    if image is None: raise FileNotFoundError('Prepare .artifacts/hand-reference.jpg first; see VALIDACAO.md')
    options=vision.HandLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=str(ROOT/'models'/'hand_landmarker.task')),num_hands=2)
    with vision.HandLandmarker.create_from_options(options) as engine:
        result=engine.detect(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)))
    assert len(result.hand_landmarks)==2
    # Bottom hand: five extended digits. Top hand: thumb flexed, four extended.
    for hand in result.hand_landmarks:
        xs=[p.x*image.shape[1] for p in hand];ys=[p.y*image.shape[0] for p in hand]
        expected=5 if sum(ys)/len(ys)>image.shape[0]/2 else 4
        crop=image[max(0,int(min(ys))-35):min(image.shape[0],int(max(ys))+35),max(0,int(min(xs))-35):min(image.shape[1],int(max(xs))+35)]
        detector=Detector('hand')
        try:
            for timestamp in range(0,1000,150): output=detector.process(crop,timestamp)
            assert output['value']==expected,(expected,output)
            print(dict(expected=expected,detected=output['value'],raised=output['raised']))
            empty=detector.process(crop*0,1200)
            assert empty['value'] is None and not empty['points']
        finally: detector.close()

if __name__=='__main__':main()
