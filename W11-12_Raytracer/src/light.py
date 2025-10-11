
from dataclasses import dataclass

import numpy as np

@dataclass
class LightSource:
    direction: np.ndarray
    color: np.ndarray

    def get_normalized_direction(self) -> np.ndarray:
        return self.direction / np.sqrt(np.dot(self.direction, self.direction))
