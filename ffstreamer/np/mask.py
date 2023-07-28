# -*- coding: utf-8 -*-

from typing import Tuple

from numpy import bool_ as np_bool
from numpy import uint8
from numpy.typing import NDArray


def split_mask_on_off(mask: NDArray[uint8]) -> Tuple[NDArray[uint8], NDArray[uint8]]:
    assert len(mask.shape) == 3
    assert mask.shape[-1] == 1

    mask_cmp: NDArray[np_bool] = mask != 0  # noqa
    mask_on = mask_cmp.astype(uint8)
    mask_off = 1 - mask_on

    assert len(mask_on.shape) == 3
    assert mask_on.shape[-1] == 1
    assert mask_on.dtype == uint8

    assert len(mask_off.shape) == 3
    assert mask_off.shape[-1] == 1
    assert mask_off.dtype == uint8

    return mask_on, mask_off  # type: ignore[return-value]
