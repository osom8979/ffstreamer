# -*- coding: utf-8 -*-

import os
from functools import lru_cache


@lru_cache
def get_assets_dir() -> str:
    return os.path.abspath(os.path.dirname(__file__))


@lru_cache
def get_big_buck_bunny_trailer_path() -> str:
    return os.path.join(get_assets_dir(), "big_buck_bunny-trailer_iphone.m4v")
