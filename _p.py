from pathlib import Path
p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\ai_api_config_gui.py")
t = p.read_text(encoding="utf-8")

old = """    def __init__(self):
        self.config_id = "default"
        self._load_config()"""
new = """    def __init__(self, runtime_overlay=None):
        self.config_id = "default"
        self.runtime_overlay = dict(runtime_overlay) if runtime_overlay else {}
        self._load_config()"""
if old not in t:
    raise SystemExit("init not found")
t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("step1 ok")
