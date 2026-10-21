"""Shopping: tracked IDs whose bounding-box center enters a calibrated region.
IDs are not identities; switches/occlusions can change totals. No direction inference.
"""
from pathlib import Path
import cv2
if __package__ in (None,''):
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from app.cli import run

MODELO = Path(__file__).resolve().parent/'models'/'yolo11n.pt'
PESSOA = 0
CONFIANCA = .3
AREA_ESCADA_BASE = [0,280,880,880]

class ShoppingProcessor:
    def __init__(self):
        if not MODELO.is_file(): raise FileNotFoundError(f'Modelo local ausente: {MODELO}')
        import os
        config=MODELO.parent.parent.parent/'.artifacts'/'ultralytics'
        config.mkdir(parents=True,exist_ok=True)
        os.environ['YOLO_OFFLINE']='true'
        os.environ['YOLO_AUTOINSTALL']='false'
        os.environ.setdefault('YOLO_CONFIG_DIR',str(config))
        from ultralytics import YOLO, settings
        settings.update({'sync':False})
        self.modelo = YOLO(str(MODELO))
        self.ids_escada = set()

    def process(self, img, timestamp=0):
        altura, largura = img.shape[:2]
        sx, sy = largura/1920, altura/1080
        ex1, ey1, ex2, ey2 = [int(v*s) for v,s in zip(AREA_ESCADA_BASE,(sx,sy,sx,sy))]
        fator = largura/1920
        escala_tela = min(1.,1280/largura)
        # Deteccao + rastreamento (cada pessoa ganha um ID que se mantem entre os frames)
        resultado = self.modelo.track(img, classes=[PESSOA], conf=CONFIANCA, persist=True, verbose=False)[0]

        na_cena = 0
        na_escada = 0
        if resultado.boxes.id is not None:
            caixas = resultado.boxes.xyxy.int().tolist()
            ids = resultado.boxes.id.int().tolist()
            for (x1, y1, x2, y2), pid in zip(caixas, ids):
                na_cena += 1
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2      # centro da pessoa
                dentro = ex1 <= cx <= ex2 and ey1 <= cy <= ey2
                if dentro:
                    na_escada += 1
                    self.ids_escada.add(pid)
                cor = (0, 165, 255) if dentro else (0, 255, 0)  # laranja = na escada
                cv2.rectangle(img, (x1, y1), (x2, y2), cor, 3)
                cv2.putText(img, f'ID {pid}', (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
                cv2.circle(img, (cx, cy), 5, cor, -1)

        # Area da escada rolante
        cv2.rectangle(img, (ex1, ey1), (ex2, ey2), (255, 0, 0), 3)
        cv2.putText(img, 'ESCADA ROLANTE', (ex1 + 10, ey1 + int(40 * fator)), cv2.FONT_HERSHEY_SIMPLEX, 1.2 * fator, (255, 0, 0), 3)

        # Painel com os numeros (canto inferior direito, onde so tem piso)
        topo = altura - int(190 * fator)
        cv2.rectangle(img, (largura - int(620 * fator), topo), (largura, altura), (255, 0, 0), -1)
        textos = [f'NA CENA: {na_cena}', f'NA ESCADA AGORA: {na_escada}', f'IDS NA REGIAO: {len(self.ids_escada)}']
        for i, t in enumerate(textos):
            cv2.putText(img, t, (largura - int(600 * fator), topo + int((55 + i * 55) * fator)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4 * fator, (255, 255, 255), max(1, int(4 * fator)))

        if escala_tela < 1:
            img = cv2.resize(img, None, fx=escala_tela, fy=escala_tela)
        return img

    def close(self):
        self.ids_escada.clear()
        self.modelo = None

def main():
    run(ShoppingProcessor(), 'escadas.mp4', 'Shopping / IDs na regiao')

if __name__ == '__main__': main()
