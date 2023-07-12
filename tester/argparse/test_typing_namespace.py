# -*- coding: utf-8 -*-

from argparse import Namespace
from typing import List, Optional
from unittest import TestCase, main

from ffstreamer.argparse.typing_namespace import VALUE_SEPARATOR, typing_namespace


class TypingNamespaceTestCase(TestCase):
    def test_string(self) -> None:
        class Config(Namespace):
            default: str

            optional_yes: Optional[str]
            optional_no: Optional[str]

            list_empty: List[str]
            list_single: List[str]
            list_multiple: List[str]

            optional_list_no: Optional[List[str]]
            optional_list_empty: Optional[List[str]]
            optional_list_single: Optional[List[str]]
            optional_list_multiple: Optional[List[str]]

        namespace = Namespace(
            default="a",
            optional_yes="b",
            list_empty="",
            list_single="d",
            list_multiple=f"e{VALUE_SEPARATOR}f",
            optional_list_empty="",
            optional_list_single="h",
            optional_list_multiple=f"i{VALUE_SEPARATOR}j",
        )

        args = typing_namespace(namespace, Config)

        self.assertEqual("a", args.default)
        self.assertEqual("b", args.optional_yes)
        self.assertIsNone(args.optional_no)

        self.assertListEqual([], args.list_empty)
        self.assertListEqual(["d"], args.list_single)
        self.assertListEqual(["e", "f"], args.list_multiple)

        self.assertIsNone(args.optional_list_no)
        assert isinstance(args.optional_list_empty, list)
        assert isinstance(args.optional_list_single, list)
        assert isinstance(args.optional_list_multiple, list)
        self.assertListEqual([], args.optional_list_empty)
        self.assertListEqual(["h"], args.optional_list_single)
        self.assertListEqual(["i", "j"], args.optional_list_multiple)

    def test_boolean(self) -> None:
        class Config(Namespace):
            default: bool

            optional_yes: Optional[bool]
            optional_no: Optional[bool]

            list_empty: List[bool]
            list_single: List[bool]
            list_multiple: List[bool]

            optional_list_no: Optional[List[bool]]
            optional_list_empty: Optional[List[bool]]
            optional_list_single: Optional[List[bool]]
            optional_list_multiple: Optional[List[bool]]

        namespace = Namespace(
            default="True",
            optional_yes="True",
            list_empty="",
            list_single="True",
            list_multiple=f"True{VALUE_SEPARATOR}False",
            optional_list_empty="",
            optional_list_single="True",
            optional_list_multiple=f"True{VALUE_SEPARATOR}False",
        )

        args = typing_namespace(namespace, Config)

        self.assertTrue(args.default)
        self.assertTrue(args.optional_yes)
        self.assertIsNone(args.optional_no)

        self.assertListEqual([], args.list_empty)
        self.assertListEqual([True], args.list_single)
        self.assertListEqual([True, False], args.list_multiple)

        self.assertIsNone(args.optional_list_no)
        assert isinstance(args.optional_list_empty, list)
        assert isinstance(args.optional_list_single, list)
        assert isinstance(args.optional_list_multiple, list)
        self.assertListEqual([], args.optional_list_empty)
        self.assertListEqual([True], args.optional_list_single)
        self.assertListEqual([True, False], args.optional_list_multiple)

    def test_integer(self) -> None:
        class Config(Namespace):
            default: int

            optional_yes: Optional[int]
            optional_no: Optional[int]

            list_empty: List[int]
            list_single: List[int]
            list_multiple: List[int]

            optional_list_no: Optional[List[int]]
            optional_list_empty: Optional[List[int]]
            optional_list_single: Optional[List[int]]
            optional_list_multiple: Optional[List[int]]

        namespace = Namespace(
            default="1",
            optional_yes="2",
            list_empty="",
            list_single="3",
            list_multiple=f"4{VALUE_SEPARATOR}5",
            optional_list_empty="",
            optional_list_single="6",
            optional_list_multiple=f"7{VALUE_SEPARATOR}8",
        )

        args = typing_namespace(namespace, Config)

        self.assertEqual(1, args.default)
        self.assertEqual(2, args.optional_yes)
        self.assertIsNone(args.optional_no)

        self.assertListEqual([], args.list_empty)
        self.assertListEqual([3], args.list_single)
        self.assertListEqual([4, 5], args.list_multiple)

        self.assertIsNone(args.optional_list_no)
        assert isinstance(args.optional_list_empty, list)
        assert isinstance(args.optional_list_single, list)
        assert isinstance(args.optional_list_multiple, list)
        self.assertListEqual([], args.optional_list_empty)
        self.assertListEqual([6], args.optional_list_single)
        self.assertListEqual([7, 8], args.optional_list_multiple)

    def test_floating(self) -> None:
        class Config(Namespace):
            default: float

            optional_yes: Optional[float]
            optional_no: Optional[float]

            list_empty: List[float]
            list_single: List[float]
            list_multiple: List[float]

            optional_list_no: Optional[List[float]]
            optional_list_empty: Optional[List[float]]
            optional_list_single: Optional[List[float]]
            optional_list_multiple: Optional[List[float]]

        namespace = Namespace(
            default="1.1",
            optional_yes="2.2",
            list_empty="",
            list_single="3.3",
            list_multiple=f"4.4{VALUE_SEPARATOR}5.5",
            optional_list_empty="",
            optional_list_single="6.6",
            optional_list_multiple=f"7.7{VALUE_SEPARATOR}8.8",
        )

        args = typing_namespace(namespace, Config)

        self.assertEqual(1.1, args.default)
        self.assertEqual(2.2, args.optional_yes)
        self.assertIsNone(args.optional_no)

        self.assertListEqual([], args.list_empty)
        self.assertListEqual([3.3], args.list_single)
        self.assertListEqual([4.4, 5.5], args.list_multiple)

        self.assertIsNone(args.optional_list_no)
        assert isinstance(args.optional_list_empty, list)
        assert isinstance(args.optional_list_single, list)
        assert isinstance(args.optional_list_multiple, list)
        self.assertListEqual([], args.optional_list_empty)
        self.assertListEqual([6.6], args.optional_list_single)
        self.assertListEqual([7.7, 8.8], args.optional_list_multiple)


if __name__ == "__main__":
    main()
