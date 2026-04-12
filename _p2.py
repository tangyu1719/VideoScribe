from pathlib import Path
p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\ai_api_config_gui.py")
t = p.read_text(encoding="utf-8")

old2 = """        except Exception as e:
            print(f"[AI API Config] 加载配置失败: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self):"""
new2 = """        except Exception as e:
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
                    "id": str(__import__("uuid").uuid4()),
                    "name": "来自 config.json 的备用接入点",
                    "api_key": r.get("volcengine_api_key") or self.config.get("api_key", ""),
                    "base_url": self.config.get("base_url", ""),
                    "model": self.config.get("model", ""),
                    "endpoint_id": r["ai_chat_model_backup"],
                    "created_at": __import__("datetime").datetime.now().isoformat(),
                }
            ]

    def _get_default_config(self):"""
if old2 not in t:
    raise SystemExit("load tail not found")
t = t.replace(old2, new2, 1)

old3 = """class AIAPIConfigWindow:
    """AI API配置窗口"""
    
    def __init__(self, parent, config_manager=None):
        self.parent = parent
        self.config_manager = config_manager or AIAPIConfigManager()
        self.config = self.config_manager.get_config()
        self.backup_frames = []
        
        self._create_window()"""
new3 = """class AIAPIConfigWindow:
    """AI API配置窗口"""

    def __init__(self, parent, config_manager=None, on_save_runtime=None):
        self.parent = parent
        self.on_save_runtime = on_save_runtime
        self.config_manager = config_manager or AIAPIConfigManager()
        self.config = self.config_manager.get_config()
        self.backup_frames = []

        self._create_window()"""
# fix docstring - use escaped quotes in heredoc - the old3 has """ inside - problem

