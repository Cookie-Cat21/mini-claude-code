import os
import unittest
from unittest import mock


class TestCollectApiKeys(unittest.TestCase):
    def test_single_key(self) -> None:
        with mock.patch.dict(os.environ, {"FOO_API_KEY": "abc", "FOO_API_KEYS": ""}):
            from keys import collect_api_keys

            self.assertEqual(collect_api_keys("FOO_API_KEY", "FOO_API_KEYS"), ["abc"])

    def test_multi_dedupes_and_order(self) -> None:
        env = {
            "FOO_API_KEY": "first",
            "FOO_API_KEYS": "first, second, third",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            from keys import collect_api_keys

            self.assertEqual(collect_api_keys("FOO_API_KEY", "FOO_API_KEYS"), ["first", "second", "third"])

    def test_newline_in_bulk(self) -> None:
        env = {"FOO_API_KEY": "", "FOO_API_KEYS": "a\nb,c"}
        with mock.patch.dict(os.environ, env, clear=False):
            from keys import collect_api_keys

            self.assertEqual(collect_api_keys("FOO_API_KEY", "FOO_API_KEYS"), ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
