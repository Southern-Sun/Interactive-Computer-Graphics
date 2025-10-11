
from dataclasses import dataclass

import numpy as np

class LightSource:
    direction: np.ndarray
    color: np.ndarray
