"""
AI API配置管理模块 - 用于video_gui的AI设置界面
支持主配置和多个备选配置，持久化到MariaDB
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import uuid
from datetime import datetime

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
                    'base_url': row['base_url'] or 'https://ark.cn-beijing.volces.com/api/v3',
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

    def _get_default_config(self):
        """获取默认配置"""
        return {
            'id': self.config_id,
            'name': '火山引擎',
            'api_key': '',
            'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
            'model': 'Doubao-Seed-2.0-mini',
            'endpoint_id': 'ep-20260411182220-jv5qt',
            'request_format': 'openai',
            'enabled': True,
            'backup_configs': []
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
        self.window.title("AI API配置")
        self.window.geometry("800x700")
        self.window.resizable(True, True)
        self.window.configure(bg="#f0f4f8")
        
        # 主容器
        main_frame = tk.Frame(self.window, bg="#f0f4f8")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_label = tk.Label(
            main_frame,
            text="AI API配置中心",
            font=("微软雅黑", 16, "bold"),
            fg="#0066cc",
            bg="#f0f4f8"
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

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

        # 创建画布和滚动条
        canvas = tk.Canvas(main_frame, bg="#f0f4f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 内容容器
        self.content_frame = tk.Frame(canvas, bg="#f0f4f8")
        canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW, width=740)
        
        # 绑定滚动
        self.content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        
        # 主配置区域
        self._create_main_config_section()
        
        # 分隔线
        separator = tk.Frame(self.content_frame, bg="#cccccc", height=1)
        separator.pack(fill=tk.X, pady=20)
        
        # 备选配置区域
        self._create_backup_config_section()
        
        # 按钮区域
        button_frame = tk.Frame(self.window, bg="#f0f4f8")
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        save_btn = tk.Button(
            button_frame,
            text="💾 保存配置",
            command=self._save_config,
            bg="#0066cc",
            fg="white",
            font=("微软雅黑", 11, "bold"),
            padx=20,
            pady=8,
            cursor="hand2"
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="取消",
            command=self.window.destroy,
            bg="#e0e0e0",
            fg="#333",
            font=("微软雅黑", 11),
            padx=20,
            pady=8,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        # 显示数量
        self.count_label = tk.Label(
            backup_section,
            text=f"当前备选配置数量: {len(self.backup_frames)}",
            font=("微软雅黑", 9),
            fg="#666",
            bg="#ffffff"
        )
        self.count_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _load_backup_configs(self):
        """加载备选配置到界面"""
        backups = self.config.get('backup_configs', [])
        for backup in backups:
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
        """删除备选配置框架"""
        frame.destroy()
        self.backup_frames.remove(frame)
        self._update_count_label()
    
    def _update_count_label(self):
        """更新数量标签"""
        self.count_label.config(text=f"当前备选配置数量: {len(self.backup_frames)}")
    
    def _save_config(self):
        """保存配置"""
        # 收集主配置
        main_config = {
            'id': self.config.get('id', 'default'),
            'name': self.name_entry.get().strip(),
            'api_key': self.api_key_entry.get().strip(),
            'base_url': self.base_url_entry.get().strip(),
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
