# -*- coding: utf-8 -*-
import unittest

from lark_publish.feishu_target_url import TargetKind, parse_feishu_target


class TestParseFeishuTarget(unittest.TestCase):
    def test_drive_folder_url(self):
        t = parse_feishu_target(
            "https://xxx.feishu.cn/drive/folder/fldcnAbCdEfGhIjKlMnOpQr"
        )
        self.assertEqual(t.kind, TargetKind.DRIVE_FOLDER)
        self.assertEqual(t.folder_token, "fldcnAbCdEfGhIjKlMnOpQr")

    def test_drive_folder_url_non_fld_prefix(self):
        url = "https://dvnrviz26l5.feishu.cn/drive/folder/SH9EfE9Itl0yd1dsdbWcvR9ynTb"
        t = parse_feishu_target(url)
        self.assertEqual(t.kind, TargetKind.DRIVE_FOLDER)
        self.assertEqual(t.folder_token, "SH9EfE9Itl0yd1dsdbWcvR9ynTb")

    def test_drive_folder_larksuite(self):
        t = parse_feishu_target(
            "https://larksuite.com/drive/folder/fldcnZZZ"
        )
        self.assertEqual(t.kind, TargetKind.DRIVE_FOLDER)

    def test_wiki_node(self):
        t = parse_feishu_target("https://feishu.cn/wiki/wikcn0123456789abcde")
        self.assertEqual(t.kind, TargetKind.WIKI_NODE)
        self.assertEqual(t.wiki_node, "wikcn0123456789abcde")

    def test_wiki_node_new_token_with_query(self):
        url = (
            "https://dvnrviz26l5.feishu.cn/wiki/YhzqwByshiRNWKk0T1GcxFHmn6b"
            "?table=tblFCGNZ972sgTe5&view=vew0F5khI8"
        )
        t = parse_feishu_target(url)
        self.assertEqual(t.kind, TargetKind.WIKI_NODE)
        self.assertEqual(t.wiki_node, "YhzqwByshiRNWKk0T1GcxFHmn6b")

    def test_wiki_node_new_token_bare(self):
        t = parse_feishu_target("YhzqwByshiRNWKk0T1GcxFHmn6b")
        self.assertEqual(t.kind, TargetKind.WIKI_NODE)
        self.assertEqual(t.wiki_node, "YhzqwByshiRNWKk0T1GcxFHmn6b")

    def test_wiki_space_settings(self):
        t = parse_feishu_target(
            "https://bytedance.feishu.cn/wiki/settings/7000000000000123456"
        )
        self.assertEqual(t.kind, TargetKind.WIKI_SPACE)
        self.assertEqual(t.wiki_space, "7000000000000123456")

    def test_bare_folder_token(self):
        t = parse_feishu_target("fldcnX")
        self.assertEqual(t.kind, TargetKind.DRIVE_FOLDER)

    def test_bare_wiki_node(self):
        t = parse_feishu_target("wikcnAbcd")
        self.assertEqual(t.kind, TargetKind.WIKI_NODE)

    def test_bare_space_id(self):
        t = parse_feishu_target("7000000000000999999")
        self.assertEqual(t.kind, TargetKind.WIKI_SPACE)

    def test_wiki_settings_rejected_as_node(self):
        with self.assertRaises(ValueError):
            parse_feishu_target("https://x.feishu.cn/wiki/settings/123")

    def test_unknown(self):
        with self.assertRaises(ValueError):
            parse_feishu_target("https://x.feishu.cn/docx/doxcnXXX")

    def test_my_library_bare(self):
        t = parse_feishu_target("my_library")
        self.assertEqual(t.kind, TargetKind.WIKI_SPACE)
        self.assertEqual(t.wiki_space, "my_library")


if __name__ == "__main__":
    unittest.main()
