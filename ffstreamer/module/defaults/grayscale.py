# -*- coding: utf-8 -*-

import numpy as np

__version__ = "1.0.0"
__doc__ = "Grayscale converter"


def on_frame(data: np.ndarray) -> np.ndarray:
    return np.stack((data.mean(axis=-1),) * 3, axis=-1).astype(dtype=np.uint8)
