#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tk/Windows GUI 宏观测试执行器（可复用）

目标：
- 用“场景 JSON”定义 GUI 测试步骤，而不是写死单个 case。
- 统一输出截图证据与 JSON 报告，形成可回放闭环。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class GuiMacroError(RuntimeError):
    """GUI 宏执行错误。"""


@dataclass
class StepResult:
    index: int
    action: str
    status: str
    elapsed_ms: int
    detail: str = ""
    screenshot: str = ""


@dataclass
class RunReport:
    scenario: str
    started_at: str
    finished_at: str = ""
    success: bool = False
    steps: List[StepResult] = field(default_factory=list)
    artifacts_dir: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario": self.scenario,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "success": self.success,
            "artifacts_dir": self.artifacts_dir,
            "steps": [s.__dict__ for s in self.steps],
        }


class GuiMacroRunner:
    """场景执行器。"""

    def __init__(self, scenario_path: Path, artifacts_dir: Path):
        self.scenario_path = scenario_path
        self.scenario = self._load_scenario(scenario_path)
        self.artifacts_dir = artifacts_dir
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.proc: Optional[subprocess.Popen] = None
        self.main_window = None

        self.pywinauto_desktop = None
        self.pywinauto_application = None
        self.pyautogui = None

    @staticmethod
    def _load_scenario(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _lazy_import_tools(self):
        if self.pywinauto_desktop is None:
            try:
                from pywinauto import Desktop, Application  # type: ignore
                self.pywinauto_desktop = Desktop
                self.pywinauto_application = Application
            except Exception as e:
                raise GuiMacroError(
                    f"缺少 pywinauto 或导入失败：{e}。请先安装 `pip install pywinauto`"
                )
        if self.pyautogui is None:
            try:
                import pyautogui  # type: ignore
                pyautogui.FAILSAFE = True
                self.pyautogui = pyautogui
            except Exception as e:
                raise GuiMacroError(
                    f"缺少 pyautogui 或导入失败：{e}。请先安装 `pip install pyautogui pillow`"
                )

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def _take_screenshot(self, name: str) -> str:
        self._lazy_import_tools()
        file_name = f"{self._timestamp()}-{name}.png"
        out_path = self.artifacts_dir / file_name
        self.pyautogui.screenshot(str(out_path))
        return str(out_path)

    def _action_launch_app(self, step: Dict[str, Any]):
        command = step.get("command")
        if not command:
            raise GuiMacroError("launch_app 缺少 command")
        cwd = step.get("cwd") or str(Path(command).parent)
        use_shell = bool(step.get("shell", False))
        cmd = command
        if isinstance(command, str) and not use_shell:
            cmd = shlex.split(command, posix=False)
        self.proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=use_shell,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        wait_sec = float(step.get("wait_sec", 3))
        time.sleep(wait_sec)

    def _action_attach_main_window(self, step: Dict[str, Any]):
        self._lazy_import_tools()
        title_re = step.get("title_re")
        if not title_re:
            raise GuiMacroError("attach_main_window 缺少 title_re")
        # 优先按当前启动进程附着，避免粘到历史窗口
        if self.proc and self.proc.poll() is None:
            try:
                app = self.pywinauto_application(backend="uia").connect(process=self.proc.pid)
                win = app.top_window()
                if not title_re or re.search(title_re, win.window_text()):
                    self.main_window = win
                    self.main_window.set_focus()
                    return
            except Exception:
                pass
        timeout_sec = float(step.get("timeout_sec", 20))
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                win = self.pywinauto_desktop(backend="uia").window(title_re=title_re)
                if win.exists(timeout=0.5):
                    self.main_window = win
                    self.main_window.set_focus()
                    return
            except Exception:
                pass
            time.sleep(0.4)
        raise GuiMacroError(f"未找到主窗口: title_re={title_re}")

    def _action_close_windows_by_title(self, step: Dict[str, Any]):
        """清理历史窗口，避免附着到旧实例。"""
        self._lazy_import_tools()
        title_re = step.get("title_re")
        if not title_re:
            raise GuiMacroError("close_windows_by_title 缺少 title_re")
        pattern = re.compile(title_re)
        closed = 0
        pids = set()
        for w in self.pywinauto_desktop(backend="uia").windows():
            try:
                title = w.window_text() or ""
                if not pattern.search(title):
                    continue
                pids.add(w.process_id())
                try:
                    w.close()
                    closed += 1
                except Exception:
                    pass
            except Exception:
                pass
        # 兜底杀进程
        for pid in pids:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass
        time.sleep(float(step.get("wait_sec", 1)))

    def _click_by_text(self, text_re: str, timeout_sec: float = 8.0):
        if self.main_window is None:
            raise GuiMacroError("未附着主窗口，请先执行 attach_main_window")
        pattern = re.compile(text_re)
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                # 先尝试直接查找
                ctrl = self.main_window.child_window(title_re=text_re)
                if ctrl.exists(timeout=0.2):
                    ctrl.wrapper_object().click_input()
                    return
            except Exception:
                pass
            # 再做全量 descendant 扫描，兼容 Tk 场景
            try:
                for c in self.main_window.descendants():
                    text = ""
                    try:
                        text = (c.window_text() or "").strip()
                    except Exception:
                        text = ""
                    if text and pattern.search(text):
                        c.wrapper_object().click_input()
                        return
            except Exception:
                pass
            time.sleep(0.2)
        raise GuiMacroError(f"点击失败，未找到控件文本: {text_re}")

    def _action_click_text(self, step: Dict[str, Any]):
        text_re = step.get("text_re")
        if not text_re:
            raise GuiMacroError("click_text 缺少 text_re")
        self._click_by_text(text_re, float(step.get("timeout_sec", 8)))

    def _action_assert_text(self, step: Dict[str, Any]):
        text_re = step.get("text_re")
        if not text_re:
            raise GuiMacroError("assert_text 缺少 text_re")
        if self.main_window is None:
            raise GuiMacroError("未附着主窗口，请先执行 attach_main_window")
        pattern = re.compile(text_re)
        timeout_sec = float(step.get("timeout_sec", 8))
        start = time.time()
        while time.time() - start < timeout_sec:
            try:
                ctrl = self.main_window.child_window(title_re=text_re)
                if ctrl.exists(timeout=0.2):
                    return
            except Exception:
                pass
            try:
                for c in self.main_window.descendants():
                    text = ""
                    try:
                        text = (c.window_text() or "").strip()
                    except Exception:
                        text = ""
                    if text and pattern.search(text):
                        return
            except Exception:
                pass
            time.sleep(0.2)
        raise GuiMacroError(f"断言失败，未找到文本: {text_re}")

    def _action_wait(self, step: Dict[str, Any]):
        time.sleep(float(step.get("sec", 1)))

    def _action_screenshot(self, step: Dict[str, Any]) -> str:
        name = step.get("name", "manual")
        return self._take_screenshot(name)

    def _action_close_app(self, step: Dict[str, Any]):
        _ = step
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()

    def run(self) -> RunReport:
        report = RunReport(
            scenario=str(self.scenario_path),
            started_at=datetime.now().isoformat(),
            artifacts_dir=str(self.artifacts_dir),
        )

        action_map = {
            "launch_app": self._action_launch_app,
            "close_windows_by_title": self._action_close_windows_by_title,
            "attach_main_window": self._action_attach_main_window,
            "click_text": self._action_click_text,
            "assert_text": self._action_assert_text,
            "wait": self._action_wait,
            "screenshot": self._action_screenshot,
            "close_app": self._action_close_app,
        }

        ok = True
        steps = self.scenario.get("steps", [])
        for i, step in enumerate(steps, start=1):
            action = step.get("action", "")
            started = time.time()
            shot = ""
            try:
                if action not in action_map:
                    raise GuiMacroError(f"不支持的 action: {action}")
                result = action_map[action](step)
                if isinstance(result, str):
                    shot = result
                elapsed = int((time.time() - started) * 1000)
                report.steps.append(
                    StepResult(
                        index=i,
                        action=action,
                        status="passed",
                        elapsed_ms=elapsed,
                        screenshot=shot,
                    )
                )
            except Exception as e:
                ok = False
                elapsed = int((time.time() - started) * 1000)
                fail_shot = self._take_screenshot(f"step{i}-failed")
                report.steps.append(
                    StepResult(
                        index=i,
                        action=action,
                        status="failed",
                        elapsed_ms=elapsed,
                        detail=str(e),
                        screenshot=fail_shot,
                    )
                )
                break
            finally:
                if step.get("auto_screenshot", False):
                    auto_shot = self._take_screenshot(f"step{i}-{action}")
                    report.steps[-1].screenshot = auto_shot

        # 尽量收尾
        try:
            self._action_close_app({})
        except Exception:
            pass

        report.success = ok
        report.finished_at = datetime.now().isoformat()
        report_file = self.artifacts_dir / "result.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        return report


def main():
    parser = argparse.ArgumentParser(description="GUI 宏观测试执行器")
    parser.add_argument("--scenario", required=True, help="场景 JSON 文件路径")
    parser.add_argument("--artifacts-dir", default="tests/gui/artifacts/latest", help="截图与报告输出目录")
    args = parser.parse_args()

    scenario_path = Path(args.scenario).resolve()
    artifacts_dir = Path(args.artifacts_dir).resolve()

    runner = GuiMacroRunner(scenario_path, artifacts_dir)
    report = runner.run()
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    main()

