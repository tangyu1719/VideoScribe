from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable, Dict, Optional

from .node_registry import build_task_node_docs_markdown, get_default_task_nodes


class TaskNodeCenterWindow:
    def __init__(
        self,
        parent: tk.Misc,
        config_getter: Callable[[], Dict[str, Any]],
        config_saver: Callable[[Dict[str, Any]], bool],
        logger: Optional[Callable[[str], None]] = None,
    ):
        self.parent = parent
        self._get_config = config_getter
        self._save_config = config_saver
        self._log = logger
        self.nodes = get_default_task_nodes()
        self.node_by_id = {n.node_id: n for n in self.nodes}

        self.win = tk.Toplevel(parent)
        self.win.title("本地任务编排节点中心")
        self.win.geometry("980x620")
        self.win.configure(bg="#f4f4f5")
        self.win.transient(parent)

        self.local_mode_var = tk.BooleanVar(value=False)
        self._node_overrides: Dict[str, Dict[str, Any]] = {}
        self._node_enabled: Dict[str, bool] = {}
        self._load_from_config()
        self._build()

    def _load_from_config(self) -> None:
        cfg = self._get_config() or {}
        self.local_mode_var.set(bool(cfg.get("local_workflow_mode_enabled", False)))
        self._node_overrides = dict(cfg.get("local_workflow_node_defaults", {}) or {})
        self._node_enabled = dict(cfg.get("local_workflow_node_enabled", {}) or {})

    def _build(self) -> None:
        top = tk.Frame(self.win, bg="#f4f4f5")
        top.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Checkbutton(
            top,
            text="启用本地任务编排模式（保留原固定流程，作为并行扩展入口）",
            variable=self.local_mode_var,
            bg="#f4f4f5",
            anchor="w",
        ).pack(side=tk.LEFT)

        body = tk.Frame(self.win, bg="#f4f4f5")
        body.pack(fill=tk.BOTH, expand=True, padx=14, pady=8)

        left = tk.Frame(body, bg="#ffffff", highlightbackground="#e4e4e7", highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(left, text="任务节点", bg="#ffffff", font=("Microsoft YaHei UI", 10, "bold")).pack(
            anchor="w", padx=10, pady=(10, 6)
        )
        self.listbox = tk.Listbox(left, width=34, activestyle="none")
        self.listbox.pack(fill=tk.Y, padx=10, pady=(0, 10))
        for node in self.nodes:
            tag = "启用" if self._node_enabled.get(node.node_id, True) else "停用"
            self.listbox.insert(tk.END, f"{node.title} [{tag}]")
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        if self.nodes:
            self.listbox.selection_set(0)

        right = tk.Frame(body, bg="#ffffff", highlightbackground="#e4e4e7", highlightthickness=1)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.detail = tk.Text(right, wrap=tk.WORD, font=("Consolas", 10), bd=0)
        self.detail.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btns = tk.Frame(self.win, bg="#f4f4f5")
        btns.pack(fill=tk.X, padx=14, pady=(0, 12))
        tk.Button(btns, text="配置当前节点输入参数", command=self._open_param_editor).pack(side=tk.LEFT)
        tk.Button(btns, text="启用/停用当前节点", command=self._toggle_current).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="导出节点文档", command=self._export_docs).pack(side=tk.LEFT, padx=8)
        tk.Button(btns, text="保存配置", command=self._save).pack(side=tk.RIGHT)

        self._render_selected()

    def _selected_node_id(self) -> Optional[str]:
        idxs = self.listbox.curselection()
        if not idxs:
            return None
        return self.nodes[idxs[0]].node_id

    def _on_select(self, _evt: Any) -> None:
        self._render_selected()

    def _render_selected(self) -> None:
        node_id = self._selected_node_id()
        if not node_id:
            return
        node = self.node_by_id[node_id]
        enabled = self._node_enabled.get(node_id, True)
        overrides = self._node_overrides.get(node_id, {})
        lines = [
            f"节点: {node.title} ({node.node_id})",
            f"阶段: {node.stage}",
            f"状态: {'启用' if enabled else '停用'}",
            "",
            f"说明: {node.description}",
            "",
            "[输入参数]",
        ]
        for p in node.input_params:
            cur = overrides.get(p.name, p.default)
            lines.append(
                f"- {p.name} ({p.type}) {'必填' if p.required else '可选'}"
                f"\n  说明: {p.description}"
                f"\n  当前值: {cur!r}"
            )
        lines.append("")
        lines.append("[输出字段]")
        for p in node.output_fields:
            lines.append(f"- {p.name} ({p.type})：{p.description}")

        self.detail.config(state=tk.NORMAL)
        self.detail.delete("1.0", tk.END)
        self.detail.insert(tk.END, "\n".join(lines))
        self.detail.config(state=tk.DISABLED)

    def _open_param_editor(self) -> None:
        node_id = self._selected_node_id()
        if not node_id:
            return
        node = self.node_by_id[node_id]
        top = tk.Toplevel(self.win)
        top.title(f"输入参数配置 - {node.title}")
        top.geometry("640x420")
        top.transient(self.win)

        cur = dict(self._node_overrides.get(node_id, {}))
        vars_map: Dict[str, tk.StringVar] = {}
        row = 0
        for p in node.input_params:
            tk.Label(top, text=f"{p.name} ({p.type})").grid(row=row, column=0, sticky="w", padx=12, pady=(10, 2))
            val = cur.get(p.name, p.default)
            sv = tk.StringVar(value="" if val is None else str(val))
            vars_map[p.name] = sv
            tk.Entry(top, textvariable=sv, width=70).grid(row=row + 1, column=0, sticky="we", padx=12)
            tk.Label(top, text=p.description, fg="#6b7280").grid(row=row + 2, column=0, sticky="w", padx=12)
            row += 3

        def _save_param() -> None:
            dst = self._node_overrides.setdefault(node_id, {})
            for p in node.input_params:
                raw = vars_map[p.name].get().strip()
                if p.type == "int":
                    dst[p.name] = int(raw) if raw else p.default
                elif p.type == "bool":
                    dst[p.name] = raw.lower() in ("1", "true", "yes", "y")
                elif p.type in ("object", "array"):
                    if not raw:
                        dst[p.name] = p.default
                    else:
                        try:
                            dst[p.name] = json.loads(raw)
                        except Exception as e:
                            messagebox.showerror("参数错误", f"{p.name} 不是合法 JSON：{e}")
                            return
                else:
                    dst[p.name] = raw
            self._render_selected()
            top.destroy()

        tk.Button(top, text="保存当前节点参数", command=_save_param).grid(row=row + 1, column=0, sticky="e", padx=12, pady=12)

    def _toggle_current(self) -> None:
        node_id = self._selected_node_id()
        if not node_id:
            return
        cur = bool(self._node_enabled.get(node_id, True))
        self._node_enabled[node_id] = not cur
        idx = self.listbox.curselection()[0]
        node = self.node_by_id[node_id]
        tag = "启用" if self._node_enabled[node_id] else "停用"
        self.listbox.delete(idx)
        self.listbox.insert(idx, f"{node.title} [{tag}]")
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self._render_selected()

    def _export_docs(self) -> None:
        docs = build_task_node_docs_markdown(self.nodes)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_dir = os.path.join(base_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        out = os.path.join(docs_dir, "task_nodes.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(docs)
        messagebox.showinfo("导出完成", f"节点文档已生成:\n{out}")
        if self._log:
            self._log(f"任务节点文档已导出：{out}")

    def _save(self) -> None:
        cfg = dict(self._get_config() or {})
        cfg["local_workflow_mode_enabled"] = bool(self.local_mode_var.get())
        cfg["local_workflow_node_defaults"] = self._node_overrides
        cfg["local_workflow_node_enabled"] = self._node_enabled
        ok = self._save_config(cfg)
        if ok:
            if self._log:
                self._log("本地任务编排配置已保存")
            messagebox.showinfo("保存成功", "本地任务编排配置已写入 config。")
        else:
            messagebox.showwarning("保存失败", "配置写入失败，请检查日志。")


def open_task_node_center(
    parent: tk.Misc,
    config_getter: Callable[[], Dict[str, Any]],
    config_saver: Callable[[Dict[str, Any]], bool],
    logger: Optional[Callable[[str], None]] = None,
) -> None:
    TaskNodeCenterWindow(parent, config_getter=config_getter, config_saver=config_saver, logger=logger)

