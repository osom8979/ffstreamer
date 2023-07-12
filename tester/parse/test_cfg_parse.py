# -*- coding: utf-8 -*-

import os
from tempfile import NamedTemporaryFile
from unittest import TestCase, main

from ffstreamer.parse.cfg_parse import (
    CFG_SECTION,
    get_cfg_section_by_path,
    get_cfg_section_by_text,
)

TEST_CFG_CONTENT = f"""
[{CFG_SECTION}]
aaa=test
bbb="777"
ccc=888
"""


class CfgParseTestCase(TestCase):
    def setUp(self):
        fp = NamedTemporaryFile(delete=False)
        fp.write(TEST_CFG_CONTENT.encode("utf-8"))
        fp.close()
        self.test_cfg_path = fp.name

    def tearDown(self):
        os.unlink(self.test_cfg_path)
        self.assertFalse(os.path.exists(self.test_cfg_path))

    def test_get_cfg_section_by_path(self):
        config = get_cfg_section_by_path(self.test_cfg_path, section=CFG_SECTION)
        self.assertEqual(3, len(config))
        self.assertEqual("test", config["aaa"])
        self.assertEqual('"777"', config["bbb"])
        self.assertEqual("888", config["ccc"])

    def test_get_cfg_section_by_text(self):
        config = get_cfg_section_by_text(TEST_CFG_CONTENT, section=CFG_SECTION)
        self.assertEqual(3, len(config))
        self.assertEqual("test", config["aaa"])
        self.assertEqual('"777"', config["bbb"])
        self.assertEqual("888", config["ccc"])


if __name__ == "__main__":
    main()
