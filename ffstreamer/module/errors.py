# -*- coding: utf-8 -*-

from typing import Optional


class ModuleError(Exception):
    def __init__(self, plugin: str, *args: str):
        super().__init__(*args)
        self.plugin = plugin


# ---------------
# Attribute Error
# ---------------


class ModuleAttributeError(ModuleError):
    def __init__(self, plugin: str, attribute: str, detail: str):
        super().__init__(plugin, f"Plugin[{plugin}.{attribute}] {detail}")
        self.attribute = attribute


class ModuleAttributeNotFoundError(ModuleAttributeError):
    def __init__(self, plugin: str, attribute: str):
        super().__init__(plugin, attribute, "Attribute not found")


class ModuleAttributeInvalidValueError(ModuleAttributeError):
    def __init__(self, plugin: str, attribute: str, detail: Optional[str] = None):
        prefix = "The attribute value is invalid"
        message = f"{prefix}: {detail}" if detail else prefix
        super().__init__(plugin, attribute, message)


# --------------
# Callback Error
# --------------


class ModuleCallbackError(ModuleError):
    def __init__(self, plugin: str, callback: str, detail: str):
        super().__init__(plugin, f"Plugin[{plugin}.{callback}] {detail}")
        self.callback = callback


class ModuleCallbackInvalidStateError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str, detail: Optional[str] = None):
        prefix = "Invalid state"
        message = f"{prefix}: {detail}" if detail else prefix
        super().__init__(plugin, callback, message)


class ModuleCallbackAlreadyStateError(ModuleCallbackInvalidStateError):
    def __init__(self, plugin: str, callback: str):
        super().__init__(plugin, callback, "Already state")


class ModuleCallbackNotReadyStateError(ModuleCallbackInvalidStateError):
    def __init__(self, plugin: str, callback: str):
        super().__init__(plugin, callback, "Not ready state")


class ModuleCallbackNotFoundError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str):
        super().__init__(plugin, callback, "Callback not found")


class ModuleCallbackNotCoroutineError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str):
        super().__init__(plugin, callback, "The callback must be a coroutine")


class ModuleCallbackCoroutineError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str):
        super().__init__(plugin, callback, "The callback must not be a coroutine")


class ModuleCallbackRuntimeError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str):
        super().__init__(plugin, callback, "A runtime error occurred in the callback")


class ModuleCallbackInvalidReturnValueError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str, detail: Optional[str] = None):
        prefix = "The return value of the callback is invalid"
        message = f"{prefix}: {detail}" if detail else prefix
        super().__init__(plugin, callback, message)


class ModuleCallbackNotFoundRouteError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str, method: str, path: str):
        message = f"Not found route: method='{method}', path='{path}'"
        super().__init__(plugin, callback, message)


class ModuleCallbackRouteRuntimeError(ModuleCallbackError):
    def __init__(self, plugin: str, callback: str, method: str, path: str):
        prefix = "A runtime error occurred in the route"
        message = f"{prefix}: method='{method}', path='{path}'"
        super().__init__(plugin, callback, message)
