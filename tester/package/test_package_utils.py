# -*- coding: utf-8 -*-

import os
from importlib import import_module
from unittest import TestCase, main

from ffstreamer import apps as ffstreamer_apps
from ffstreamer.package.package_utils import (
    all_module_names,
    filter_module_names,
    get_module_directory,
    list_submodule_names,
    list_submodule_names_with_module_path,
)


class PackageUtilsTestCase(TestCase):
    def test_get_ffstreamer_module_directory(self):
        module_directory = get_module_directory(import_module("ffstreamer"))
        self.assertTrue(os.path.isdir(module_directory))

    def test_get_module_directory(self):
        self.assertTrue(os.path.isdir(get_module_directory(ffstreamer_apps)))

    def test_list_submodule_names(self):
        modules = list_submodule_names(ffstreamer_apps)
        modules.sort()
        apps = ["files", "inspect", "modules", "pipe", "pixels", "pyav"]
        self.assertListEqual(apps, modules)

        modules2 = list_submodule_names_with_module_path("ffstreamer.apps")
        self.assertListEqual(modules2, modules)

    def test_all_module_names(self):
        self.assertIn("pip", all_module_names())
        self.assertIn("setuptools", all_module_names())

    def test_filter_module_names(self):
        self.assertIn("setuptools", filter_module_names("setup"))
        self.assertNotIn(
            "setuptools",
            filter_module_names("setup", denies=[r".*tool.*"]),
        )
        self.assertNotIn(
            "setuptools",
            filter_module_names("setup", allows=[r"NO_ANY"]),
        )


if __name__ == "__main__":
    main()
