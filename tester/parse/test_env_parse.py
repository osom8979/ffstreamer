# -*- coding: utf-8 -*-

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from ffstreamer.parse.env_parse import (
    ENVIRONMENT_FILE_PREFIX,
    ENVIRONMENT_FILE_SUFFIX,
    ENVIRONMENT_PREFIX,
    ENVIRONMENT_SUFFIX,
    get_env,
    get_file_env,
)
from ffstreamer.system.environ import exchange_env


class GetEnvNamespaceEnvironTestCase(TestCase):
    MODULE_KEY = f"{ENVIRONMENT_PREFIX}MODULE{ENVIRONMENT_SUFFIX}"

    def setUp(self):
        self.module_key = "module"
        self.module_value = "test"
        self.original_module = exchange_env(self.MODULE_KEY, self.module_value)

        self.prefix = ENVIRONMENT_PREFIX
        self.suffix = ENVIRONMENT_SUFFIX
        self.assertEqual(
            self.module_value,
            get_env(self.module_key, prefix=self.prefix, suffix=self.suffix),
        )

    def tearDown(self):
        exchange_env(self.MODULE_KEY, self.original_module)

    def test_default(self):
        value = get_env(self.module_key, prefix=self.prefix, suffix=self.suffix)
        self.assertEqual(self.module_value, value)


class GetFileEnvNamespaceEnvironTestCase(TestCase):
    MODULE_FILE_KEY = f"{ENVIRONMENT_FILE_PREFIX}MODULE{ENVIRONMENT_FILE_SUFFIX}"

    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.secret_path = Path(self.tmpdir.name) / "secret"
        self.secret_value = "test"
        self.secret_path.write_text(self.secret_value)
        self.assertTrue(self.secret_path.exists())

        self.module_key = "module"
        self.module_value = str(self.secret_path)
        self.original_module = exchange_env(self.MODULE_FILE_KEY, self.module_value)

        self.prefix = ENVIRONMENT_FILE_PREFIX
        self.suffix = ENVIRONMENT_FILE_SUFFIX
        self.assertEqual(
            self.module_value,
            get_env(self.module_key, prefix=self.prefix, suffix=self.suffix),
        )

    def tearDown(self):
        exchange_env(self.MODULE_FILE_KEY, self.original_module)
        self.tmpdir.cleanup()
        self.assertFalse(self.secret_path.exists())

    def test_default(self):
        self.assertEqual(
            self.secret_value,
            get_file_env(self.module_key, prefix=self.prefix, suffix=self.suffix),
        )


if __name__ == "__main__":
    main()
