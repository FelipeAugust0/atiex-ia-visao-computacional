"""Explicit, opt-in preparation. Never called by the application."""
from pathlib import Path
import urllib.request

def main():
    folder=Path(__file__).resolve().parent/'models'
    folder.mkdir(exist_ok=True)
    for name,url in {
        'hand_landmarker.task':'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
        'pose_landmarker_full.task':'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task',
    }.items():
        target=folder/name
        if target.exists(): print(f'Preservado: {target}'); continue
        temporary=target.with_suffix('.download')
        try:
            urllib.request.urlretrieve(url,temporary)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
        print(f'Preparado: {target}')

if __name__=='__main__': main()
