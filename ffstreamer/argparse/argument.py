# -*- coding: utf-8 -*-

from typing import List


def argument_splitter(arg: str, **kwargs) -> List[str]:
    result = list()
    for a in arg.format(**kwargs).split():
        stripped_arg = a.strip()
        if stripped_arg:
            result.append(stripped_arg)
    return result
