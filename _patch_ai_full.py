# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\ai_api_config_gui.py")
t = p.read_text(encoding="utf-8")

old_early = """        if not DB_AVAILABLE:
            # 使用默认配置
            self.config = self._get_default_config()
            return"""
new_early = """        if not DB_AVAILABLE:
            # 使用默认配置
            self.config = self._get_default_config()
            self._merge_runtime_overlay()
            return"""
if old_early not in t:
    raise SystemExit("early return not found")
t = t.replace(old_early, new_early, 1)

old_tail = """        except Exception as e:
            print(f"[AI API Config] 加载配置失败: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self):"""
new_tail = """        except Exception as e:
            print(f"[AI API Config] 加载配置失败: {e}")
            self.config = self._get_default_config()

        self._merge_runtime_overlay()

    def _merge_runtime_overlay(self):
        r = self.runtime_overlay
        if not r:
            return
        if r.get("volcengine_api_key"):
            self.config["api_key"] = r["volcengine_api_key"]
        if r.get("ai_chat_model"):
            self.config["endpoint_id"] = r["ai_chat_model"]
        if r.get("volcengine_base_url"):
            self.config["base_url"] = r["volcengine_base_url"]
        if r.get("ai_chat_model_display_name"):
            self.config["model"] = r["ai_chat_model_display_name"]
        backups = self.config.get("backup_configs") or []
        if not backups and r.get("ai_chat_model_backup"):
            self.config["backup_configs"] = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "来自 config.json 的备用接入点",
                    "api_key": r.get("volcengine_api_key") or self.config.get("api_key", ""),
                    "base_url": self.config.get("base_url", ""),
                    "model": self.config.get("model", ""),
                    "endpoint_id": r["ai_chat_model_backup"],
                    "created_at": datetime.now().isoformat(),
                }
            ]

    def _get_default_config(self):"""
if old_tail not in t:
    raise SystemExit("tail not found")
t = t.replace(old_tail, new_tail, 1)

win_old = """class AIAPIConfigWindow:
    \"\"\"AI API配置窗口\"\"\"
    
    def __init__(self, parent, config_manager=None):
        self.parent = parent
        self.config_manager = config_manager or AIAPIConfigManager()
        self.config = self.config_manager.get_config()
        self.backup_frames = []
        
        self._create_window()"""
win_new = """class AIAPIConfigWindow:
    \"\"\"AI API配置窗口\"\"\"

    def __init__(self, parent, config_manager=None, on_save_runtime=None):
        self.parent = parent
        self.on_save_runtime = on_save_runtime
        self.config_manager = config_manager or AIAPIConfigManager()
        self.config = self.config_manager.get_config()
        self.backup_frames = []

        self._create_window()"""
if win_old not in t:
    raise SystemExit("window init not found")
t = t.replace(win_old, win_new, 1)

anc = """        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # 创建画布和滚动条"""
anc_new = """        title_label.pack(anchor=tk.W, pady=(0, 10))

        hint = tk.Label(
            main_frame,
            text="说明：数据库 llm_configs 与程序实际使用的 config.json 可能不一致；"
            "打开本窗口时已用当前运行中的接入点覆盖展示。保存时将同时尝试写数据库并同步 config.json。",
            font=("微软雅黑", 9),
            fg="#666666",
            bg="#f0f4f8",
            wraplength=720,
            justify=tk.LEFT,
        )
        hint.pack(anchor=tk.W, pady=(0, 12))

        # 创建画布和滚动条"""
if anc not in t:
    raise SystemExit("title anchor not found")
t = t.replace(anc, anc_new, 1)

t = t.replace(
    'values=["openai", "azure"]',
    'values=["openai", "azure", "custom"]',
    1,
)

sv_old = """        # 保存到管理器
        self.config_manager.config = main_config
        if self.config_manager._save_to_db():
            messagebox.showinfo("成功", "AI API配置已保存到数据库！")
            self.window.destroy()
        else:
            messagebox.showerror("错误", "保存配置失败，请检查数据库连接！")"""
sv_new = """        # 保存到管理器
        self.config_manager.config = main_config
        db_ok = self.config_manager._save_to_db()
        if callable(self.on_save_runtime):
            try:
                self.on_save_runtime(main_config, backup_configs)
            except Exception as ex:
                messagebox.showerror("错误", f"同步 config.json 失败：{ex}")
                return
        if db_ok:
            messagebox.showinfo("成功", "AI API配置已保存到数据库，并已同步 config.json。")
        else:
            messagebox.showwarning(
                "已保存到本地",
                "数据库不可用或写入失败，已仅将主/备用接入点同步到 config.json；请检查 MariaDB 或 db 模块。",
            )
        self.window.destroy()"""
if sv_old not in t:
    raise SystemExit("save block not found")
t = t.replace(sv_old, sv_new, 1)

op_old = """def open_ai_api_config_window(parent):
    \"\"\"打开AI API配置窗口的便捷函数\"\"\"
    AIAPIConfigWindow(parent)"""
op_new = """def open_ai_api_config_window(parent, get_runtime_config=None, on_save_runtime=None):
    \"\"\"get_runtime_config 返回 dict（如 CONFIG），与数据库合并展示；保存时写回 config.json。\"\"\"
    overlay = get_runtime_config() if callable(get_runtime_config) else None
    mgr = AIAPIConfigManager(runtime_overlay=overlay)
    AIAPIConfigWindow(parent, config_manager=mgr, on_save_runtime=on_save_runtime)"""
if op_old not in t:
    raise SystemExit("open not found")
t = t.replace(op_old, op_new, 1)

p.write_text(t, encoding="utf-8")
print("ai_api_config_gui patched")
