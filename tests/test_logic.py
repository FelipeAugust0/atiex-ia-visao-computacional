import math
import pytest
from app.logic import JumpCounter, HandStabilizer, FingerFilter, fingers_up

def pose(opened=False):
    p=[[.5,.4,0,1] for _ in range(33)]
    coords={11:(.42,.3),12:(.58,.3),23:(.44,.55),24:(.56,.55),25:(.44,.7),26:(.56,.7),27:(.45,.9),28:(.55,.9),13:(.42,.43),14:(.58,.43),15:(.42,.59),16:(.58,.59)}
    if opened: coords.update({13:(.32,.2),14:(.68,.2),15:(.22,.1),16:(.78,.1),27:(.3,.9),28:(.7,.9)})
    for i,(x,y) in coords.items(): p[i]=[x,y,0,1]
    return p

def hold(counter,p,n=3):
    for _ in range(n): counter.update(p)

def test_complete_and_held():
    c=JumpCounter();hold(c,pose());hold(c,pose(True),40)
    assert c.count==0
    hold(c,pose());assert c.count==1
    hold(c,pose(),40);assert c.count==1
    hold(c,pose(True));hold(c,pose());assert c.count==2

def test_incomplete_and_initial_open():
    c=JumpCounter();hold(c,pose(True));hold(c,pose());assert c.count==0
    p=pose(True);p[15]=[.4,.45,0,1];hold(c,p);hold(c,pose());assert c.count==0

def test_legs_only_and_hands_together_below_head():
    c=JumpCounter();hold(c,pose())
    p=pose();p[27][0]=.25;p[28][0]=.75;p[15]=[.49,.59,0,1];p[16]=[.51,.59,0,1]
    hold(c,p);hold(c,pose());assert c.count==0

@pytest.mark.parametrize('lost',[None,[]])
def test_lost_detection(lost):
    c=JumpCounter();hold(c,pose());hold(c,pose(True));c.update(lost);hold(c,pose());assert c.count==0

def test_low_confidence_and_framing():
    c=JumpCounter();hold(c,pose());hold(c,pose(True));p=pose(True);p[27][3]=.2
    assert c.update(p)=='Enquadre o corpo inteiro'
    hold(c,pose());assert c.count==0

def test_stabilizer():
    s=HandStabilizer()
    assert s.update(0,0) is None
    assert s.update(0,300)==0
    assert s.update(1,400) is None
    assert s.update(0,450) is None
    assert s.update(0,760)==0
    assert s.update(None,800) is None
    assert s.update(5,900) is None
    assert s.update(5,1201)==5

def hand(extended):
    p=[[0,0,0] for _ in range(21)]
    p[1]=[-.3,.3,0];p[2]=[-.6,.55,0];p[3]=[-.9,.8,0];p[4]=[-1.2,1.05,0] if extended else [-.1,.7,0]
    for x,m,j,d,t in [(-.45,5,6,7,8),(0,9,10,11,12),(.35,13,14,15,16),(.65,17,18,19,20)]:
        p[m]=[x,1,0];p[j]=[x,1.5,0];p[d]=[x,1.9,0] if extended else [x,1.2,.2];p[t]=[x,2.3,0] if extended else [x,.9,.3]
    return p

@pytest.mark.parametrize('rotation',[0,.6,1.7,3.14])
@pytest.mark.parametrize('mirror',[-1,1])
def test_fingers_orientation(rotation,mirror):
    for extended in [True,False]:
        p=[[mirror*(x*math.cos(rotation)-y*math.sin(rotation)),x*math.sin(rotation)+y*math.cos(rotation),z] for x,y,z in hand(extended)]
        assert fingers_up(p)==[extended]*5

@pytest.mark.parametrize('number',range(6))
def test_each_number(number):
    closed=hand(False);opened=hand(True)
    for i,group in enumerate([(1,2,3,4),(5,6,7,8),(9,10,11,12),(13,14,15,16),(17,18,19,20)]):
        if i<number:
            for j in group:closed[j]=opened[j]
    assert sum(fingers_up(closed))==number

def test_fast_open_peak_and_relaxed_standing_width():
    c=JumpCounter();closed=pose()
    closed[27][0]=.39;closed[28][0]=.61  # natural stance, not perfectly touching feet
    hold(c,closed)
    c.update(pose(True))  # only one sampled frame at the peak
    hold(c,closed)
    assert c.count==1

def test_uncertain_elbow_does_not_discard_visible_body():
    c=JumpCounter();hold(c,pose());p=pose(True)
    p[13][3]=.4;p[25][3]=.4
    c.update(p);hold(c,pose())
    assert c.count==1

def test_open_arms_without_wider_legs_never_counts():
    c=JumpCounter();hold(c,pose());p=pose(True)
    p[27][0]=.45;p[28][0]=.55
    hold(c,p);hold(c,pose());assert c.count==0

def test_finger_filter_glitch_and_loss():
    f=FingerFilter();base=[False,True,True,True,True];glitch=[True]*5
    assert f.update(base)==base
    assert f.update(glitch)==base
    assert f.update(base)==base
    assert f.update(glitch)==base
    assert f.update(glitch)==glitch
    assert f.update(None)==[]
    assert f.update(base)==base
