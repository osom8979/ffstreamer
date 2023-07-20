# -*- coding: utf-8 -*-

import os
from importlib import import_module
from unittest import TestCase, main

from ffstreamer import apps as ffstreamer_app
from ffstreamer.package.package_utils import (
    all_module_names,
    filter_module_names,
    get_module_directory,
    list_submodule_names,
)


class PackageUtilsTestCase(TestCase):
    def test_get_ffstreamer_module_directory(self):
        module_directory = get_module_directory(import_module("ffstreamer"))
        self.assertTrue(os.path.isdir(module_directory))

    def test_get_module_directory(self):
        self.assertTrue(os.path.isdir(get_module_directory(ffstreamer_app)))

    def test_list_submodule_names(self):
        modules = list_submodule_names(ffstreamer_app)
        modules.sort()
        self.assertListEqual(["files", "inspect", "modules", "pixels", "run"], modules)

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
