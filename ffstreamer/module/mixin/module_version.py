# -*- coding: utf-8 -*-

from ffstreamer.module.errors import (
    ModuleAttributeInvalidValueError,
    ModuleAttributeNotFoundError,
)
from ffstreamer.module.mixin._module_base import ModuleBase
from ffstreamer.module.variables import NAME_VERSION


class ModuleVersion(ModuleBase):
    def get_version(self) -> str:
        if not self.has(NAME_VERSION):
            raise ModuleAttributeNotFoundError(self.module_name, NAME_VERSION)

        value = self.get(NAME_VERSION)

        if value is None:
            raise ModuleAttributeInvalidValueError(
                self.module_name,
                NAME_VERSION,
                "It must not be of `None`",
            )

        if not isinstance(value, str):
            raise ModuleAttributeInvalidValueError(
                self.module_name,
                NAME_VERSION,
                "The attribute must be of type `str`",
            )

        return value

    @property
    def version(self) -> str:
        try:
            return self.get_version()
        except:  # noqa
            return str()
