"""Shared finite, exception-safe terminal video runner."""
import argparse
from pathlib import Path
import cv2

def run(processor, default, title):
    parser=argparse.ArgumentParser(description=title)
    parser.add_argument('source',nargs='?',default=default)
    parser.add_argument('--headless',action='store_true',help='Processa sem abrir janela')
    parser.add_argument('--max-frames',type=int,default=0)
    try:
        args=parser.parse_args()
    except BaseException:
        processor.close()
        raise
    source=args.source
    if source.isdigit(): source=int(source)
    elif not Path(source).is_file(): source=str(Path(__file__).resolve().parent/'assets'/source)
    cap=cv2.VideoCapture(source)
    try:
        if not cap.isOpened(): raise RuntimeError(f'Não foi possível abrir a câmera/vídeo: {source}')
        fps=cap.get(cv2.CAP_PROP_FPS)
        fps=fps if 0<fps<240 else 30
        n=0
        while True:
            ok,frame=cap.read()
            if not ok:
                if n==0: raise RuntimeError('Nenhum quadro legível na origem.')
                break
            n+=1
            frame=processor.process(frame,round(n*1000/fps))
            if not args.headless:
                cv2.imshow(title,frame)
                if cv2.waitKey(max(1,round(1000/fps)))&255==ord('q'): break
            if args.max_frames and n>=args.max_frames: break
        print(f'Quadros processados: {n}')
    finally:
        cap.release(); processor.close()
        if not args.headless: cv2.destroyAllWindows()
