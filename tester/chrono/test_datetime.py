# -*- coding: utf-8 -*-

from unittest import TestCase, main

from ffstreamer.chrono.datetime import tznow


class DatetimeTestCase(TestCase):
    def test_default(self):
        self.assertIsNotNone(tznow().tzinfo)


if __name__ == "__main__":
    main()
