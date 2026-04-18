# -*- coding: utf-8 -*-
"""飞书上传模块回归：Mock 模式、路径解析、URL 解析 fldcn。"""
import os
import sys
import unittest

# 与 video_gui / 定时任务同目录运行
_AGENT = os.path.dirname(os.path.abspath(__file__))
if _AGENT not in sys.path:
    sys.path.insert(0, _AGENT)


class TestFeishuIntegration(unittest.TestCase):
    def setUp(self):
        self._old_mock = os.environ.pop("FEISHU_MOCK_UPLOAD", None)

    def tearDown(self):
        if self._old_mock is not None:
            os.environ["FEISHU_MOCK_UPLOAD"] = self._old_mock
        else:
            os.environ.pop("FEISHU_MOCK_UPLOAD", None)

    def test_mock_upload_returns_token(self):
        os.environ["FEISHU_MOCK_UPLOAD"] = "1"
        from feishu_integration import FeishuKnowledgeBase

        kb = FeishuKnowledgeBase("id", "sec")
        self.assertEqual(
            kb.upload_document("标题", "# 正文", feishu_folder_path="任意"),
            "mock_doc_token_ok",
        )

    def test_parse_prompt_folder(self):
        from feishu_integration import FeishuKnowledgeBase

        kb = FeishuKnowledgeBase("id", "sec")
        self.assertIsNone(kb.parse_feishu_folder_from_prompt(""))
        self.assertEqual(
            kb.parse_feishu_folder_from_prompt("飞书路径：就业知识库/子目录"),
            "就业知识库/子目录",
        )

    def test_extract_drive_folder_from_url(self):
        from feishu_integration import FeishuKnowledgeBase

        url = "https://bytedance.feishu.cn/drive/folder/fldcnxxxxxxxxxxxx"
        tok = FeishuKnowledgeBase._extract_drive_folder_token(url)
        self.assertEqual(tok, "fldcnxxxxxxxxxxxx")

    def test_extract_drive_folder_non_fld_prefix_url(self):
        from feishu_integration import FeishuKnowledgeBase

        url = "https://dvnrviz26l5.feishu.cn/drive/folder/SH9EfE9Itl0yd1dsdbWcvR9ynTb"
        self.assertEqual(
            FeishuKnowledgeBase._extract_drive_folder_token(url),
            "SH9EfE9Itl0yd1dsdbWcvR9ynTb",
        )

    def test_extract_bare_fldcn(self):
        from feishu_integration import FeishuKnowledgeBase

        self.assertEqual(
            FeishuKnowledgeBase._extract_drive_folder_token("fldcnAbCdEfGh"),
            "fldcnAbCdEfGh",
        )

    def test_wiki_path_segments(self):
        from feishu_integration import FeishuKnowledgeBase

        kb = FeishuKnowledgeBase("a", "b")
        self.assertEqual(
            kb._wiki_parse_path_segments("就业技术文档集/AI相关"),
            ["就业技术文档集", "AI相关"],
        )


if __name__ == "__main__":
    unittest.main()
