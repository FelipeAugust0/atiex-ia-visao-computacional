"""Regression landmarks inferred from the public MediaPipe example image.

The image itself is not redistributed. This checks classification on real model
output, not model accuracy on an unseen webcam population.
"""
import json
from pathlib import Path
import pytest
from app.logic import fingers_up

SAMPLES=json.loads((Path(__file__).parent/'fixtures'/'hands_reference.json').read_text())

@pytest.mark.parametrize('sample',SAMPLES)
@pytest.mark.parametrize('mirror',[-1,1])
def test_real_landmarks(sample,mirror):
    p=[[mirror*x,y,z] for x,y,z in sample['points']]
    assert sum(fingers_up(p))==sample['expected']
