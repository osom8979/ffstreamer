# -*- coding: utf-8 -*-

from multiprocessing import Event as NewEvent
from multiprocessing.synchronize import Event


def create_event() -> Event:
    return NewEvent()
