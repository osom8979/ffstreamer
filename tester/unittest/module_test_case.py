# -*- coding: utf-8 -*-

import os
from unittest import IsolatedAsyncioTestCase

from ffstreamer.package.package_utils import get_module_directory
from ffstreamer.system.path_context import PathContext
from tester.unittest import modules


class ModuleIsolatedAsyncioTestCase(IsolatedAsyncioTestCase):
    def setUp(self):
        self._modules_dir = get_module_directory(modules)
        self._path_context = PathContext(self._modules_dir, insert_operation=True)
        self._path_context.open()

        for module in self.test_module_names:
            self.assertTrue(os.path.isdir(os.path.join(self._modules_dir, module)))

    def tearDown(self):
        self._path_context.close()

    @property
    def plugins_dir(self) -> str:
        return self._modules_dir

    def _assert_modules_name(self, name: str) -> str:
        self.assertTrue(name)
        module_dir = os.path.join(self._modules_dir, name)
        self.assertTrue(os.path.isdir(module_dir))
        module_init_file = os.path.join(module_dir, "__init__.py")
        self.assertTrue(os.path.isfile(module_init_file))
        return name

    @property
    def ffstreamer_test_default(self):
        return self._assert_modules_name("ffstreamer_test_default")

    @property
    def test_module_names(self):
        return [self.ffstreamer_test_default]
