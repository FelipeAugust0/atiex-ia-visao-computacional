"""Geometry and temporal state, independent of cameras and inference engines."""
import math

POSE_EDGES = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),(23,24),(23,25),(25,27),(24,26),(26,28)]
HAND_EDGES = [(0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(0,17),(17,18),(18,19),(19,20)]

def distance(a,b):
    return math.dist(a[:3],b[:3])

def angle(a,b,c):
    u=[x-y for x,y in zip(a[:3],b[:3])]
    v=[x-y for x,y in zip(c[:3],b[:3])]
    denominator=math.sqrt(sum(x*x for x in u)*sum(x*x for x in v))
    return math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(u,v))/denominator)))) if denominator else 0

class JumpCounter:
    def __init__(self):
        self.count=0
        self.phase='waiting'
        self.candidate=None
        self.streak=0
        self.baseline=None

    def update(self, points, width=1, height=1):
        # Knees/elbows are often assigned lower visibility even in a usable pose.
        required=[11,12,15,16,23,24,27,28]
        if not points:
            self.phase='waiting'; self.streak=0; self.candidate=None; self.baseline=None
            return 'Nenhuma pessoa detectada'
        if any(points[i][3]<.45 or not 0<points[i][0]<1 or not 0<points[i][1]<1 for i in required):
            self.phase='waiting'; self.streak=0; self.candidate=None; self.baseline=None
            return 'Enquadre o corpo inteiro'
        p=[(v[0]*width,v[1]*height,0) for v in points]
        torso=(distance(p[11],p[23])+distance(p[12],p[24]))/2
        if torso<1e-5:
            self.phase='waiting'
            return 'Enquadre o corpo inteiro'
        spread=distance(p[27],p[28])/torso
        straight=angle(p[11],p[13],p[15])>110 and angle(p[12],p[14],p[16])>110
        raised=all(p[w][1]<p[s][1]-.3*torso and p[e][1]<p[s][1]+.1*torso for s,e,w in [(11,13,15),(12,14,16)])
        lowered=all(p[w][1]>p[s][1]+.45*torso for s,w in [(11,15),(12,16)])
        shoulder=distance(p[11],p[12])/torso
        baseline=self.baseline
        close_limit=max(.9,shoulder*1.25) if baseline is None else baseline+.2
        open_limit=max(.85,(baseline or .4)+.3,(baseline or .4)*1.5)
        pose='open' if straight and raised and spread>open_limit else 'closed' if lowered and spread<close_limit else None
        self.streak=self.streak+1 if pose==self.candidate else 1
        self.candidate=pose
        # At 8–12 fps an open peak may occupy just one frame. Closing still needs
        # confirmation, so a held pose or an isolated closed frame cannot count.
        if self.streak>=(1 if pose=='open' else 2):
            if pose=='closed':
                if self.phase=='open': self.count+=1
                self.phase='closed'
                self.baseline=spread if baseline is None else .85*baseline+.15*spread
            elif pose=='open' and self.phase=='closed': self.phase='open'
        if self.phase=='waiting': return 'Comece com braços baixos e pés juntos'
        if self.phase=='open': return 'Abertura reconhecida. Agora feche braços e pernas'
        if not raised: return 'Pronto. Leve as duas mãos acima da cabeça'
        if spread<=open_limit: return 'Afaste mais os pés ao levantar os braços'
        return 'Estenda os braços acima da cabeça'

def fingers_up(p):
    """Palm-facing geometry in an aspect-corrected image plane.

    Use the PIP bend plus extension from each knuckle, rather than requiring
    both estimated 3D joints to be almost perfectly straight.
    """
    scale=distance(p[0],p[9])
    if scale<1e-6: return [False]*5
    palm_width=distance(p[5],p[17])
    # A straight thumb folded across the palm must not be treated as raised.
    thumb=(angle(p[1],p[2],p[4])>130 and angle(p[2],p[3],p[4])>135
           and distance(p[4],p[5])>.4*scale
           and distance(p[4],p[17])>1.15*palm_width)
    return [thumb]+[angle(p[m],p[j],p[t])>145
                   and distance(p[m],p[t])>1.45*distance(p[m],p[j])
                   and distance(p[0],p[t])>distance(p[0],p[j])+.05*scale
                   for m,j,t in [(5,6,8),(9,10,12),(13,14,16),(17,18,20)]]

class FingerFilter:
    """Require two agreeing observations to change an individual finger."""
    def __init__(self):
        self.values=None
        self.streak=[0]*5

    def update(self, values):
        if values is None:
            self.values=None; self.streak=[0]*5
            return []
        if self.values is None:
            self.values=list(values)
        for i,value in enumerate(values):
            self.streak[i]=self.streak[i]+1 if value!=self.values[i] else 0
            if self.streak[i]>=2:
                self.values[i]=value; self.streak[i]=0
        return list(self.values)

class HandStabilizer:
    def __init__(self):
        self.candidate=None; self.since=0; self.value=None

    def update(self, value, timestamp):
        if value is None:
            self.candidate=None; self.value=None; self.since=timestamp
        elif value!=self.candidate:
            self.candidate=value; self.since=timestamp; self.value=None
        elif timestamp-self.since>=300:
            self.value=value
        return self.value
