#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新增工具节点与常用工具回归测试（不依赖GUI启动）
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cursor_tools.tools import read_file_tool_impl, replace_in_file_tool_impl, terminal_tool_impl, write_file_tool_impl
from video_gui import App


class _FakePage:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.last_xhs = None

    def append_log(self, *_args, **_kwargs):
        return None

    def download_video(self, link: str):
        p = self.base_dir / "fake_video.mp4"
        p.write_bytes(b"fake")
        return str(p)

    def speech_to_text(self, _video_file: str, _user_prompt: str = ""):
        return {"transcript": "SENTINEL_TRANSCRIPT"}

    def summarize_with_volcengine(self, transcript: str, _prompt: str = ""):
        return f"SUMMARY::{transcript[:32]}"

    def generate_md(self, result_data: dict, link: str, platform: str):
        p = self.base_dir / "out.md"
        p.write_text(
            f"# {platform}\n\nlink={link}\n\nsummary={result_data.get('ai_summary','')}\n",
            encoding="utf-8",
        )
        return str(p)

    def _detect_platform(self, _link: str):
        return "测试平台"

    def _run_xiaohongshu_analysis(self, link: str, user_prompt: str, feishu_folder_path: str, analyzed_result: dict):
        self.last_xhs = {
            "link": link,
            "user_prompt": user_prompt,
            "feishu_folder_path": feishu_folder_path,
            "analyzed_result": analyzed_result,
        }


def _assert(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)


def test_new_node_tools():
    with tempfile.TemporaryDirectory(prefix="tool-nodes-") as td:
        base = Path(td)
        page = _FakePage(base)

        # 1) 多模态转文本（plain_text 路径）
        out1 = App._tool_node_multimodal_to_text(
            page,
            {},
            {"input_mode": "plain_text", "input_text": "hello multimodal", "result_data": {}},
        )
        _assert(out1.get("status") == "success", "multimodal_to_text 失败")

        # 2) 链接多模态路由工具（视频分支）
        fake_analyzer_video = SimpleNamespace(analyze_link=lambda _link: {"type": "video", "url": "https://v.example.com/1"})
        with patch("link_analyzer.LinkAnalyzer", return_value=fake_analyzer_video):
            out2 = App._tool_node_link_multimodal_pipeline(
                page,
                {"link": "https://origin.example.com/share"},
                {"user_prompt": "", "feishu_folder_path": "", "result_data": {}},
            )
        _assert(out2.get("status") == "success" and out2.get("route") == "video_pipeline", "link_multimodal_pipeline 视频分支失败")

        # 3) 严格视频下载（拒绝非视频）
        fake_analyzer_non_video = SimpleNamespace(analyze_link=lambda _link: {"type": "xiaohongshu", "url": "https://xhs.com/p/1"})
        with patch("link_analyzer.LinkAnalyzer", return_value=fake_analyzer_non_video):
            out3 = App._tool_node_download_video_strict(
                page,
                {"link": "https://xhs.com/share"},
                {"input_mode": "video_link"},
            )
        _assert(out3.get("status") == "rejected", "download_video_strict 未拒绝非视频链接")

        # 4) 模板控制生成（LLM调用桩）
        out4 = App._tool_node_template_controlled_doc_generation(
            page,
            {"raw_text": "raw-doc", "title": "T1"},
            {},
        )
        _assert(out4.get("status") == "success" and "final_markdown" in out4, "template_controlled_doc_generation 失败")

        # 6) OCR图片转文本（pytesseract桩）
        img = base / "img.png"
        try:
            from PIL import Image

            Image.new("RGB", (120, 40), color=(255, 255, 255)).save(img)
        except Exception:
            img.write_bytes(b"\x89PNG\r\n\x1a\n")
        with patch("video_gui.MINERU_PROCESSOR_AVAILABLE", False), patch("pytesseract.image_to_string", return_value="OCR_SENTINEL"):
            out6 = App._tool_node_image_ocr_to_text(
                page,
                {"image_path": str(img)},
                {"result_data": {}},
            )
        _assert(out6.get("status") == "success" and "OCR_SENTINEL" in out6.get("text", ""), "image_ocr_to_text 失败")


def test_common_tools():
    with tempfile.TemporaryDirectory(prefix="common-tools-") as td:
        base = Path(td)
        fp = base / "a.txt"
        _assert("写入成功" in write_file_tool_impl(str(fp), "hello", mode="overwrite"), "write 工具失败")
        _assert("1|hello" in read_file_tool_impl(str(fp), 1, 10), "read 工具失败")
        _assert("替换成功" in replace_in_file_tool_impl(str(fp), "hello", "world", count=1), "replace 工具失败")
        term_out = terminal_tool_impl("echo tool_ok", cwd=str(base), timeout_s=5)
        _assert("tool_ok" in term_out.lower(), "terminal 工具失败")


def main():
    print("=== 新增工具节点测试 ===")
    test_new_node_tools()
    print("OK: 新增节点（1/2/3/4/6）")

    print("=== 常用工具测试 ===")
    test_common_tools()
    print("OK: 常用工具（7）")

    print("ALL_OK")


if __name__ == "__main__":
    main()

