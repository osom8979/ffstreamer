# -*- coding: utf-8 -*-

import numpy as np

__version__ = "1.0.0"
__doc__ = "ndarray to bytes converter"


def on_frame(data: np.ndarray) -> bytes:
    return data.tobytes()
