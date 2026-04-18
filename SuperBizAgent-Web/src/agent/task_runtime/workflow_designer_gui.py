from __future__ import annotations

import copy
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any, Callable, Dict, List, Optional

from .node_registry import TaskNodeSpec, get_default_task_nodes


def _new_workflow_id(name: str, idx: int) -> str:
    base = "".join(ch for ch in name.lower().strip().replace(" ", "_") if ch.isalnum() or ch == "_")
    return f"{base or 'workflow'}_{idx}"


def _next_param_template(nodes_map: Dict[str, TaskNodeSpec], next_node_id: Optional[str]) -> str:
    if not next_node_id or next_node_id not in nodes_map:
        return "{}"
    n = nodes_map[next_node_id]
    tpl = {}
    for p in n.input_params:
        if p.default not in (None, ""):
            tpl[p.name] = p.default
        elif p.type == "object":
            tpl[p.name] = {}
        elif p.type == "array":
            tpl[p.name] = []
        elif p.type == "bool":
            tpl[p.name] = False
        elif p.type == "int":
            tpl[p.name] = 0
        else:
            tpl[p.name] = ""
    return json.dumps(tpl, ensure_ascii=False, indent=2)


class WorkflowDesignerWindow:
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

        self.nodes: List[TaskNodeSpec] = get_default_task_nodes()
        self.nodes_map: Dict[str, TaskNodeSpec] = {n.node_id: n for n in self.nodes}
        self.node_titles = [f"{n.title} ({n.node_id})" for n in self.nodes]

        self.cfg = dict(self._get_config() or {})
        self.workflows: Dict[str, Dict[str, Any]] = copy.deepcopy(self.cfg.get("local_workflow_definitions", {}) or {})
        self.current_wf_id: Optional[str] = None

        self.win = tk.Toplevel(parent)
        self.win.title("任务流程设计器（本地编排）")
        self.win.geometry("1180x700")
        self.win.configure(bg="#f4f4f5")
        self.win.transient(parent)
        self._build()

    def _build(self) -> None:
        top = tk.Frame(self.win, bg="#f4f4f5")
        top.pack(fill=tk.X, padx=12, pady=(10, 6))
        tk.Label(top, text="流程名称", bg="#f4f4f5").pack(side=tk.LEFT)
        self.wf_name_var = tk.StringVar()
        tk.Entry(top, textvariable=self.wf_name_var, width=30).pack(side=tk.LEFT, padx=8)
        tk.Button(top, text="新建流程", command=self._create_workflow).pack(side=tk.LEFT)
        tk.Button(top, text="保存全部流程", command=self._save_all).pack(side=tk.RIGHT)

        body = tk.Frame(self.win, bg="#f4f4f5")
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        left = tk.Frame(body, bg="#ffffff", highlightbackground="#e4e4e7", highlightthickness=1)
        left.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(left, text="流程列表", bg="#ffffff", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(8, 4))
        self.wf_list = tk.Listbox(left, width=30, height=18)
        self.wf_list.pack(fill=tk.Y, padx=10, pady=(0, 10))
        self.wf_list.bind("<<ListboxSelect>>", self._on_workflow_select)
        tk.Button(left, text="删除流程", command=self._delete_workflow).pack(fill=tk.X, padx=10, pady=(0, 10))

        mid = tk.Frame(body, bg="#ffffff", highlightbackground="#e4e4e7", highlightthickness=1)
        mid.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))
        tk.Label(mid, text="可用任务节点", bg="#ffffff", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor=tk.W, padx=10, pady=(8, 4))
        self.node_palette = tk.Listbox(mid, width=35, height=18)
        self.node_palette.pack(fill=tk.Y, padx=10, pady=(0, 10))
        for t in self.node_titles:
            self.node_palette.insert(tk.END, t)
        tk.Button(mid, text="加入流程 >>", command=self._add_node_to_workflow).pack(fill=tk.X, padx=10, pady=(0, 10))

        right = tk.Frame(body, bg="#ffffff", highlightbackground="#e4e4e7", highlightthickness=1)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        head = tk.Frame(right, bg="#ffffff")
        head.pack(fill=tk.X, padx=10, pady=(8, 4))
        tk.Label(head, text="流程节点顺序", bg="#ffffff", font=("Microsoft YaHei UI", 10, "bold")).pack(side=tk.LEFT)

        self.step_list = tk.Listbox(right, height=12)
        self.step_list.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.step_list.bind("<<ListboxSelect>>", self._on_step_select)

        act = tk.Frame(right, bg="#ffffff")
        act.pack(fill=tk.X, padx=10, pady=(0, 6))
        tk.Button(act, text="上移", command=lambda: self._move_step(-1)).pack(side=tk.LEFT)
        tk.Button(act, text="下移", command=lambda: self._move_step(1)).pack(side=tk.LEFT, padx=6)
        tk.Button(act, text="移除节点", command=self._remove_step).pack(side=tk.LEFT)
        tk.Button(act, text="保存当前流程", command=self._save_current_workflow).pack(side=tk.RIGHT)

        cfg = tk.Frame(right, bg="#ffffff")
        cfg.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        tk.Label(cfg, text="节点配置（支持手输 JSON）", bg="#ffffff", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor=tk.W)
        self.config_text = tk.Text(cfg, wrap=tk.WORD, font=("Consolas", 10))
        self.config_text.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        tools = tk.Frame(cfg, bg="#ffffff")
        tools.pack(fill=tk.X)
        tk.Button(tools, text="写回当前节点配置", command=self._save_step_config).pack(side=tk.LEFT)
        tk.Button(tools, text="导入模板文件", command=self._import_template).pack(side=tk.LEFT, padx=6)
        tk.Button(tools, text="按下一节点生成参数模板", command=self._apply_next_node_template).pack(side=tk.LEFT, padx=6)

        self._refresh_workflow_list()

    def _refresh_workflow_list(self) -> None:
        self.wf_list.delete(0, tk.END)
        for wf_id, wf in self.workflows.items():
            self.wf_list.insert(tk.END, f"{wf.get('name', wf_id)} ({wf_id})")

    def _current_workflow(self) -> Optional[Dict[str, Any]]:
        if not self.current_wf_id:
            return None
        return self.workflows.get(self.current_wf_id)

    def _create_workflow(self) -> None:
        name = self.wf_name_var.get().strip()
        if not name:
            messagebox.showwarning("提示", "请先输入流程名称。")
            return
        wf_id = _new_workflow_id(name, len(self.workflows) + 1)
        self.workflows[wf_id] = {"name": name, "nodes": []}
        self.current_wf_id = wf_id
        self._refresh_workflow_list()
        self._refresh_step_list()

    def _delete_workflow(self) -> None:
        if not self.current_wf_id:
            return
        self.workflows.pop(self.current_wf_id, None)
        self.current_wf_id = None
        self._refresh_workflow_list()
        self.step_list.delete(0, tk.END)
        self.config_text.delete("1.0", tk.END)

    def _on_workflow_select(self, _evt: Any) -> None:
        idxs = self.wf_list.curselection()
        if not idxs:
            return
        wf_ids = list(self.workflows.keys())
        if idxs[0] < len(wf_ids):
            self.current_wf_id = wf_ids[idxs[0]]
            self._refresh_step_list()

    def _refresh_step_list(self) -> None:
        self.step_list.delete(0, tk.END)
        wf = self._current_workflow()
        if not wf:
            return
        for i, step in enumerate(wf.get("nodes", []), start=1):
            nid = step.get("node_id", "")
            title = self.nodes_map.get(nid).title if nid in self.nodes_map else nid
            self.step_list.insert(tk.END, f"{i}. {title} ({nid})")

    def _add_node_to_workflow(self) -> None:
        wf = self._current_workflow()
        if not wf:
            messagebox.showwarning("提示", "请先新建或选择一个流程。")
            return
        idxs = self.node_palette.curselection()
        if not idxs:
            return
        node = self.nodes[idxs[0]]
        step = {"node_id": node.node_id, "config": self._default_node_config(node)}
        wf.setdefault("nodes", []).append(step)
        self._refresh_step_list()

    def _default_node_config(self, node: TaskNodeSpec) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        for p in node.input_params:
            cfg[p.name] = p.default
        if node.node_id == "agent_process":
            cfg.setdefault("prompt", "你是任务编排中的 Agent 节点，请按要求处理输入。")
            cfg.setdefault("input_source", "previous_output_json")
            cfg.setdefault("output_template", "{}")
        return cfg

    def _selected_step_idx(self) -> Optional[int]:
        idxs = self.step_list.curselection()
        if not idxs:
            return None
        return idxs[0]

    def _selected_step(self) -> Optional[Dict[str, Any]]:
        wf = self._current_workflow()
        idx = self._selected_step_idx()
        if wf is None or idx is None:
            return None
        nodes = wf.get("nodes", [])
        if idx >= len(nodes):
            return None
        return nodes[idx]

    def _on_step_select(self, _evt: Any) -> None:
        step = self._selected_step()
        if not step:
            return
        self.config_text.delete("1.0", tk.END)
        self.config_text.insert(tk.END, json.dumps(step.get("config", {}), ensure_ascii=False, indent=2))

    def _save_step_config(self) -> None:
        step = self._selected_step()
        if not step:
            return
        raw = self.config_text.get("1.0", tk.END).strip() or "{}"
        try:
            data = json.loads(raw)
        except Exception as e:
            messagebox.showerror("JSON错误", f"当前配置不是合法 JSON：{e}")
            return
        step["config"] = data
        messagebox.showinfo("已写回", "当前节点配置已更新。")

    def _move_step(self, delta: int) -> None:
        wf = self._current_workflow()
        idx = self._selected_step_idx()
        if not wf or idx is None:
            return
        nodes = wf.get("nodes", [])
        ni = idx + delta
        if ni < 0 or ni >= len(nodes):
            return
        nodes[idx], nodes[ni] = nodes[ni], nodes[idx]
        self._refresh_step_list()
        self.step_list.selection_set(ni)

    def _remove_step(self) -> None:
        wf = self._current_workflow()
        idx = self._selected_step_idx()
        if not wf or idx is None:
            return
        nodes = wf.get("nodes", [])
        if idx < len(nodes):
            nodes.pop(idx)
        self._refresh_step_list()
        self.config_text.delete("1.0", tk.END)

    def _import_template(self) -> None:
        step = self._selected_step()
        if not step:
            return
        path = filedialog.askopenfilename(
            parent=self.win,
            title="导入输出模板",
            filetypes=[("JSON/文本", "*.json *.txt *.md"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("导入失败", f"读取模板文件失败：{e}")
            return
        step.setdefault("config", {})["output_template"] = content
        self._on_step_select(None)

    def _apply_next_node_template(self) -> None:
        wf = self._current_workflow()
        idx = self._selected_step_idx()
        step = self._selected_step()
        if not wf or idx is None or not step:
            return
        nodes = wf.get("nodes", [])
        next_id = None
        if idx + 1 < len(nodes):
            next_id = nodes[idx + 1].get("node_id")
        tpl = _next_param_template(self.nodes_map, next_id)
        step.setdefault("config", {})["output_template"] = tpl
        self._on_step_select(None)

    def _save_current_workflow(self) -> None:
        if not self.current_wf_id:
            return
        self._save_all(show_msg=False)
        messagebox.showinfo("保存成功", "当前流程已保存。")

    def _save_all(self, show_msg: bool = True) -> None:
        cfg = dict(self._get_config() or {})
        cfg["local_workflow_definitions"] = self.workflows
        ok = self._save_config(cfg)
        if ok and self._log:
            self._log("任务流程定义已保存")
        if show_msg:
            if ok:
                messagebox.showinfo("保存成功", "流程定义已写入配置。")
            else:
                messagebox.showwarning("保存失败", "流程定义写入失败，请检查日志。")


def open_workflow_designer(
    parent: tk.Misc,
    config_getter: Callable[[], Dict[str, Any]],
    config_saver: Callable[[Dict[str, Any]], bool],
    logger: Optional[Callable[[str], None]] = None,
) -> None:
    WorkflowDesignerWindow(parent, config_getter=config_getter, config_saver=config_saver, logger=logger)

