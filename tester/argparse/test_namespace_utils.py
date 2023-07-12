# -*- coding: utf-8 -*-

from argparse import Namespace
from unittest import TestCase, main

from ffstreamer.argparse.namespace_utils import (
    left_join,
    right_join,
    strip_none_attributes,
)


class NamespaceUtilsTestCase(TestCase):
    def test_join_default(self):
        a = Namespace()
        b = Namespace(value=1)
        c = Namespace()
        d = Namespace(value=2)
        e = Namespace()
        nss = [a, b, c, d, e]

        left = left_join(*nss)
        self.assertEqual(1, left.value)

        right = right_join(*nss)
        self.assertEqual(2, right.value)

    def test_join_default_with_none(self):
        a = None
        b = Namespace(value=1)
        c = None
        d = Namespace(value=None)
        e = None
        nss = [a, b, c, d, e]

        left = left_join(*nss)
        self.assertEqual(1, left.value)

        right = right_join(*nss)
        self.assertEqual(1, right.value)

    def test_strip_none_attributes(self):
        a = Namespace(value1=1, value2=None)
        self.assertEqual(1, getattr(a, "value1"))
        self.assertTrue(hasattr(a, "value2"))

        strip_none_attributes(a)
        self.assertEqual(1, getattr(a, "value1"))
        self.assertFalse(hasattr(a, "value2"))


if __name__ == "__main__":
    main()
