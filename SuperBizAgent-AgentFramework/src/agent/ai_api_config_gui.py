"""
AI API配置管理模块 - 用于video_gui的AI设置界面
支持主配置和多个备选配置，持久化到MariaDB
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import uuid
from datetime import datetime
import re

# 导入数据库模块
try:
    import db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[AI API Config] 数据库模块不可用")


class AIAPIConfigManager:
    """AI API配置管理器"""
    
    def __init__(self, runtime_overlay=None):
        self.config_id = "default"
        self.runtime_overlay = dict(runtime_overlay) if runtime_overlay else {}
        self._load_config()
    
    def _load_config(self):
        """从数据库加载配置"""
        if not DB_AVAILABLE:
            # 使用默认配置
            self.config = self._get_default_config()
            self._merge_runtime_overlay()
            return
        
        try:
            results = db.execute_query(
                "SELECT * FROM llm_configs WHERE id=%s OR enabled=TRUE ORDER BY created_at LIMIT 1",
                (self.config_id,)
            )
            if results:
                row = results[0]
                self.config = {
                    'id': row['id'],
                    'name': row['name'],
                    'api_key': row['api_key'] or '',
                    'base_url': _normalize_openai_base_url(row['base_url'] or 'https://ark.cn-beijing.volces.com/api/v3'),
                    'model': row['model'] or 'Doubao-Seed-2.0-mini',
                    'endpoint_id': row['endpoint_id'] or 'ep-20260411182220-jv5qt',
                    'request_format': row['request_format'] or 'openai',
                    'enabled': row['enabled'],
                    'backup_configs': json.loads(row['backup_configs']) if row['backup_configs'] else []
                }
            else:
                # 使用默认配置并保存到数据库
                self.config = self._get_default_config()
                self._save_to_db()
        except Exception as e:
            print(f"[AI API Config] 加载配置失败: {e}")
            self.config = self._get_default_config()

        self._merge_runtime_overlay()

    def _merge_runtime_overlay(self):
        r = self.runtime_overlay
        if not r:
            return
        # 运行时接入点状态（用于前端过滤不展示过期/暂停）
        if isinstance(r.get("ai_chat_model_status"), dict):
            self.config["endpoint_status"] = dict(r["ai_chat_model_status"])
        if r.get("volcengine_api_key"):
            self.config["api_key"] = r["volcengine_api_key"]
        if r.get("ai_chat_model"):
            self.config["endpoint_id"] = r["ai_chat_model"]
        if r.get("volcengine_base_url"):
            self.config["base_url"] = _normalize_openai_base_url(r["volcengine_base_url"])
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

    def _get_default_config(self):
        """获取默认配置"""
        return {
            'id': self.config_id,
            'name': '火山引擎',
            'api_key': '',
            'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
            'model': 'Doubao-Seed-2.0-pro',
            'endpoint_id': 'ep-20260413220538-pbfqw',
            'request_format': 'openai',
            'enabled': True,
            'backup_configs': [
                {
                    'id': str(uuid.uuid4()),
                    'name': 'GLM-4.7',
                    'api_key': '',
                    'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
                    'model': 'GLM-4.7',
                    'endpoint_id': 'ep-20260413220727-84n92',
                    'created_at': datetime.now().isoformat()
                },
                {
                    'id': str(uuid.uuid4()),
                    'name': 'Doubao-Seed-2.0-pro',
                    'api_key': '',
                    'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
                    'model': 'Doubao-Seed-2.0-pro',
                    'endpoint_id': 'ep-20260413220538-pbfqw',
                    'created_at': datetime.now().isoformat()
                }
            ]
        }

    def _save_to_db(self):
        """保存配置到数据库"""
        if not DB_AVAILABLE:
            print("[AI API Config] 数据库不可用，无法保存")
            return False

        try:
            sql = """
                INSERT INTO llm_configs (id, name, api_key, base_url, model, endpoint_id, request_format, enabled, backup_configs, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name=%s, api_key=%s, base_url=%s, model=%s, endpoint_id=%s, request_format=%s, enabled=%s, backup_configs=%s, updated_at=%s
            """
            now = datetime.now().isoformat()
            backup_json = json.dumps(self.config.get('backup_configs', []), ensure_ascii=False)
            params = (
                self.config['id'], self.config['name'], self.config['api_key'],
                self.config['base_url'], self.config['model'], self.config['endpoint_id'],
                self.config['request_format'], self.config['enabled'], backup_json, now,
                self.config['name'], self.config['api_key'], self.config['base_url'],
                self.config['model'], self.config['endpoint_id'], self.config['request_format'],
                self.config['enabled'], backup_json, now
            )
            db.execute_update(sql, params)
            print("[AI API Config] 配置已保存到数据库")
            return True
        except Exception as e:
            print(f"[AI API Config] 保存到数据库失败: {e}")
            return False

    def get_config(self):
        """获取当前配置"""
        return self.config.copy()

    def update_config(self, **kwargs):
        """更新配置"""
        self.config.update(kwargs)
        return self._save_to_db()

    def add_backup_config(self, name, api_key, base_url, model, endpoint_id):
        """添加备选配置"""
        backup = {
            'id': str(uuid.uuid4()),
            'name': name,
            'api_key': api_key,
            'base_url': base_url,
            'model': model,
            'endpoint_id': endpoint_id,
            'created_at': datetime.now().isoformat()
        }
        if 'backup_configs' not in self.config:
            self.config['backup_configs'] = []
        self.config['backup_configs'].append(backup)
        return self._save_to_db()

    def remove_backup_config(self, backup_id):
        """删除备选配置"""
        if 'backup_configs' in self.config:
            self.config['backup_configs'] = [
                b for b in self.config['backup_configs'] if b['id'] != backup_id
            ]
            return self._save_to_db()
        return False

    def get_backup_count(self):
        """获取备选配置数量"""
        return len(self.config.get('backup_configs', []))


def _normalize_openai_base_url(url: str) -> str:
    """避免把 /responses 或 /chat/completions 写进 base_url。"""
    u = (url or "").strip().rstrip("/")
    if not u:
        return u
    for suffix in ("/responses", "/chat/completions", "/responses/chat/completions"):
        if u.endswith(suffix):
            u = u[: -len(suffix)].rstrip("/")
    return u


class AIAPIConfigWindow:
    """AI API配置窗口"""

    def __init__(self, parent, config_manager=None, on_save_runtime=None):
        self.parent = parent
        self.on_save_runtime = on_save_runtime
        self.config_manager = config_manager or AIAPIConfigManager()
        self.config = self.config_manager.get_config()
        self.backup_frames = []

        self._create_window()
    
    def _create_window(self):
        """创建配置窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("AI API 配置")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        self.window.configure(bg="#f0f4f8")
        
        # 标题区域（页头）
        title_frame = tk.Frame(self.window, bg="#f0f4f8")
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(
            title_frame,
            text="AI API 配置中心",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 18, "bold"),
            fg="#0066cc",
            bg="#f0f4f8"
        ).pack(side=tk.LEFT)
        
        # 说明文字
        desc_frame = tk.Frame(self.window, bg="#f0f4f8")
        desc_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        tk.Label(
            desc_frame,
            text="说明：数据库 llm_configs 与程序实际使用的 config.json 可能不一致。打开本窗口时已用当前运行中的接入点覆盖展示。保存时将同时尝试写数据库并同步 config.json。",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 9),
            fg="#666666",
            bg="#f0f4f8",
            wraplength=800,
            justify=tk.LEFT
        ).pack(anchor=tk.W)
        
        # 按钮区域（统一放在页头）
        button_frame = tk.Frame(self.window, bg="#f0f4f8")
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        save_btn = tk.Button(
            button_frame,
            text="保存配置",
            command=self._save_config,
            bg="#0066cc",
            fg="white",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            overrelief=tk.RAISED
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=self.window.destroy,
            bg="#e0e0e0",
            fg="#333333",
            font=("PingFang SC, Microsoft YaHei, sans-serif", 11),
            padx=20,
            pady=8,
            cursor="hand2",
            relief=tk.FLAT,
            overrelief=tk.RAISED
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 内容区域
        self.content_frame = tk.Frame(self.window, bg="#f0f4f8")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 创建界面组件
        self._create_main_config_section()
        
        # 分隔线
        separator = tk.Frame(self.content_frame, bg="#cccccc", height=1)
        separator.pack(fill=tk.X, pady=15)
        
        # 备选配置区域
        self._create_backup_config_section()
        
        # 模态窗口
        self.window.transient(self.parent)
        self.window.grab_set()
    
    def _create_main_config_section(self):
        """创建主配置区域"""
        main_section = tk.LabelFrame(
            self.content_frame,
            text="主配置（链接生成和知识库对话共用）",
            font=("微软雅黑", 12, "bold"),
            fg="#0066cc",
            bg="#ffffff",
            padx=15,
            pady=15
        )
        main_section.pack(fill=tk.X, pady=(0, 10))
        
        # 配置名称
        tk.Label(main_section, text="配置名称:", font=("微软雅黑", 10), bg="#ffffff").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.name_entry = tk.Entry(main_section, font=("微软雅黑", 10), width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=8, padx=5)
        self.name_entry.insert(0, self.config.get('name', '火山引擎'))
        
        # API Key
        tk.Label(main_section, text="API Key:", font=("微软雅黑", 10), bg="#ffffff").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.api_key_entry = tk.Entry(main_section, font=("微软雅黑", 10), width=50, show="*")
        self.api_key_entry.grid(row=1, column=1, sticky=tk.W, pady=8, padx=5)
        self.api_key_entry.insert(0, self.config.get('api_key', ''))
        
        # Base URL
        tk.Label(main_section, text="Base URL:", font=("微软雅黑", 10), bg="#ffffff").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.base_url_entry = tk.Entry(main_section, font=("微软雅黑", 10), width=50)
        self.base_url_entry.grid(row=2, column=1, sticky=tk.W, pady=8, padx=5)
        self.base_url_entry.insert(0, self.config.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3'))
        
        # Model
        tk.Label(main_section, text="Model:", font=("微软雅黑", 10), bg="#ffffff").grid(row=3, column=0, sticky=tk.W, pady=8)
        self.model_entry = tk.Entry(main_section, font=("微软雅黑", 10), width=40)
        self.model_entry.grid(row=3, column=1, sticky=tk.W, pady=8, padx=5)
        self.model_entry.insert(0, self.config.get('model', 'Doubao-Seed-2.0-mini'))
        
        # Endpoint ID
        tk.Label(main_section, text="Endpoint ID:", font=("微软雅黑", 10), bg="#ffffff").grid(row=4, column=0, sticky=tk.W, pady=8)
        self.endpoint_entry = tk.Entry(main_section, font=("微软雅黑", 10), width=40)
        self.endpoint_entry.grid(row=4, column=1, sticky=tk.W, pady=8, padx=5)
        self.endpoint_entry.insert(0, self.config.get('endpoint_id', 'ep-20260411182220-jv5qt'))
        
        # 请求格式
        tk.Label(main_section, text="请求格式:", font=("微软雅黑", 10), bg="#ffffff").grid(row=5, column=0, sticky=tk.W, pady=8)
        self.format_var = tk.StringVar(value=self.config.get('request_format', 'openai'))
        format_combo = ttk.Combobox(main_section, textvariable=self.format_var, values=["openai", "azure", "custom"], width=15, state="readonly")
        format_combo.grid(row=5, column=1, sticky=tk.W, pady=8, padx=5)
    
    def _create_backup_config_section(self):
        """创建备选配置区域"""
        backup_section = tk.LabelFrame(
            self.content_frame,
            text="备选配置（当主配置失败时自动切换）",
            font=("微软雅黑", 12, "bold"),
            fg="#0066cc",
            bg="#ffffff",
            padx=15,
            pady=15
        )
        backup_section.pack(fill=tk.X, pady=(0, 10))
        
        # 备选配置列表容器
        self.backup_list_frame = tk.Frame(backup_section, bg="#ffffff")
        self.backup_list_frame.pack(fill=tk.X, pady=10)
        
        # 显示数量（必须先创建，避免加载备选时触发 _update_count_label 找不到控件）
        self.count_label = tk.Label(
            backup_section,
            text=f"当前备选配置数量: {len(self.backup_frames)}",
            font=("微软雅黑", 9),
            fg="#666",
            bg="#ffffff",
        )
        self.count_label.pack(anchor=tk.W, pady=(5, 0))

        # 加载现有备选配置
        self._load_backup_configs()
        
        # 添加按钮
        add_btn = tk.Button(
            backup_section,
            text="➕ 添加备选配置",
            command=self._add_backup_config,
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 10),
            padx=15,
            pady=5,
            cursor="hand2"
        )
        add_btn.pack(anchor=tk.W, pady=(10, 0))
        
        # 初次加载后刷新一次数量
        self._update_count_label()
    
    def _load_backup_configs(self):
        """加载备选配置到界面"""
        backups = self.config.get('backup_configs', [])
        status_map = self.config.get("endpoint_status") or {}

        def is_visible(endpoint_id: str) -> bool:
            if not endpoint_id:
                return True
            st = (status_map.get(endpoint_id) or "active").strip().lower()
            return st == "active"

        for backup in backups:
            # 过期/暂停的接入点不在前端展示
            if not is_visible(backup.get("endpoint_id", "")):
                continue
            self._create_backup_frame(backup)
    
    def _create_backup_frame(self, backup=None):
        """创建单个备选配置框架"""
        frame = tk.Frame(self.backup_list_frame, bg="#f5f5f5", padx=10, pady=10)
        frame.pack(fill=tk.X, pady=5)
        
        backup_id = backup.get('id', str(uuid.uuid4())) if backup else str(uuid.uuid4())
        frame.backup_id = backup_id
        
        # 配置名称
        tk.Label(frame, text="名称:", font=("微软雅黑", 9), bg="#f5f5f5").grid(row=0, column=0, sticky=tk.W)
        name_entry = tk.Entry(frame, font=("微软雅黑", 9), width=20)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        if backup:
            name_entry.insert(0, backup.get('name', ''))
        
        # API Key
        tk.Label(frame, text="API Key:", font=("微软雅黑", 9), bg="#f5f5f5").grid(row=0, column=2, sticky=tk.W, padx=(15, 0))
        key_entry = tk.Entry(frame, font=("微软雅黑", 9), width=25, show="*")
        key_entry.grid(row=0, column=3, sticky=tk.W, padx=5)
        if backup:
            key_entry.insert(0, backup.get('api_key', ''))
        
        # Model
        tk.Label(frame, text="Model:", font=("微软雅黑", 9), bg="#f5f5f5").grid(row=1, column=0, sticky=tk.W, pady=5)
        model_entry = tk.Entry(frame, font=("微软雅黑", 9), width=20)
        model_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        if backup:
            model_entry.insert(0, backup.get('model', ''))
        
        # Endpoint ID
        tk.Label(frame, text="Endpoint:", font=("微软雅黑", 9), bg="#f5f5f5").grid(row=1, column=2, sticky=tk.W, padx=(15, 0), pady=5)
        endpoint_entry = tk.Entry(frame, font=("微软雅黑", 9), width=25)
        endpoint_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        if backup:
            endpoint_entry.insert(0, backup.get('endpoint_id', ''))
        
        # 删除按钮
        delete_btn = tk.Button(
            frame,
            text="删除",
            command=lambda f=frame: self._delete_backup_frame(f),
            bg="#ff4444",
            fg="white",
            font=("微软雅黑", 8),
            padx=10,
            cursor="hand2"
        )
        delete_btn.grid(row=0, column=4, rowspan=2, padx=10)
        
        # 保存引用
        frame.entries = {
            'name': name_entry,
            'api_key': key_entry,
            'model': model_entry,
            'endpoint_id': endpoint_entry
        }
        
        self.backup_frames.append(frame)
        self._update_count_label()
    
    def _add_backup_config(self):
        """添加新的备选配置"""
        self._create_backup_frame()
    
    def _delete_backup_frame(self, frame):
        """删除备选配置框架（同时从数据中删除）"""
        # 从数据列表中删除
        backup_id = getattr(frame, 'backup_id', None)
        if backup_id and hasattr(self, 'backup_configs'):
            self.backup_configs = [b for b in self.backup_configs if b.get('id') != backup_id]
        
        # 从界面中删除
        frame.destroy()
        if frame in self.backup_frames:
            self.backup_frames.remove(frame)
        
        self._update_count_label()
    
    def _update_count_label(self):
        """更新数量标签"""
        if not hasattr(self, "count_label") or self.count_label is None:
            return
        try:
            self.count_label.config(text=f"当前备选配置数量: {len(self.backup_frames)}")
        except tk.TclError:
            pass
    
    def _save_config(self):
        """保存配置"""
        # 收集主配置
        main_config = {
            'id': self.config.get('id', 'default'),
            'name': self.name_entry.get().strip(),
            'api_key': self.api_key_entry.get().strip(),
            'base_url': _normalize_openai_base_url(self.base_url_entry.get().strip()),
            'model': self.model_entry.get().strip(),
            'endpoint_id': self.endpoint_entry.get().strip(),
            'request_format': self.format_var.get(),
            'enabled': True
        }
        
        # 收集备选配置
        backup_configs = []
        for frame in self.backup_frames:
            entries = frame.entries
            backup = {
                'id': getattr(frame, 'backup_id', str(uuid.uuid4())),
                'name': entries['name'].get().strip(),
                'api_key': entries['api_key'].get().strip(),
                'base_url': main_config['base_url'],  # 使用相同的base_url
                'model': entries['model'].get().strip(),
                'endpoint_id': entries['endpoint_id'].get().strip(),
                'created_at': datetime.now().isoformat()
            }
            if backup['name'] and backup['api_key']:  # 只保存有效的配置
                backup_configs.append(backup)

        # 强约束：确保你要求的两个接入点存在且字段规范（url/api_key 与主一致）
        must = [
            ("GLM-4.7", "GLM-4.7", "ep-20260413220727-84n92"),
            ("Doubao-Seed-2.0-pro", "Doubao-Seed-2.0-pro", "ep-20260413220538-pbfqw"),
        ]
        exist = {b.get("endpoint_id") for b in backup_configs}
        for name, model, ep in must:
            if ep not in exist:
                backup_configs.append(
                    {
                        "id": str(uuid.uuid4()),
                        "name": name,
                        "api_key": main_config["api_key"],
                        "base_url": main_config["base_url"],
                        "model": model,
                        "endpoint_id": ep,
                        "created_at": datetime.now().isoformat(),
                    }
                )
            else:
                for b in backup_configs:
                    if b.get("endpoint_id") == ep:
                        b["name"] = name
                        b["model"] = model
                        b["api_key"] = main_config["api_key"]
                        b["base_url"] = main_config["base_url"]
                        break
        
        main_config['backup_configs'] = backup_configs
        
        # 保存到管理器
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
        self.window.destroy()


def open_ai_api_config_window(parent, get_runtime_config=None, on_save_runtime=None):
    """get_runtime_config 返回 dict（如 CONFIG），与数据库合并展示；保存时写回 config.json。"""
    overlay = get_runtime_config() if callable(get_runtime_config) else None
    mgr = AIAPIConfigManager(runtime_overlay=overlay)
    AIAPIConfigWindow(parent, config_manager=mgr, on_save_runtime=on_save_runtime)


# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("测试")
    root.geometry("400x300")
    
    def open_config():
        open_ai_api_config_window(root)
    
    btn = tk.Button(root, text="打开AI API配置", command=open_config, font=("微软雅黑", 12))
    btn.pack(pady=50)
    
    root.mainloop()
