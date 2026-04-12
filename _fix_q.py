from pathlib import Path
p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py")
t = p.read_text(encoding="utf-8")
a = """self.append_log(f\"当前队列长度：{len(self.task_queue)}\")
            
            # 自动开始处理队列
            if not self.processing_queue and self.task_queue:"""
b = """self.append_log(f\"当前待处理：{self._task_queue_len()}\")
            
            # 自动开始处理队列
            if not self.processing_queue and self._task_queue_len() > 0:"""
if a not in t:
    raise SystemExit("recover block missing")
t = t.replace(a, b, 1)
old = "if not self.processing_queue and self.task_queue:\n                self.start_queue_processing()"
new = "if not self.processing_queue and self._task_queue_len() > 0:\n                self.start_queue_processing()"
count = t.count(old)
if count < 2:
    raise SystemExit(f"continue blocks count {count}")
t = t.replace(old, new, 2)
t = t.replace(
    "                if self.task_queue and not self.processing_queue:",
    "                if self._task_queue_len() > 0 and not self.processing_queue:",
    1,
)
# shrink path - two occurrences of "if self.task_queue:" in update_thread - be careful
t = t.replace(
    "                if self.task_queue:\n                    # 如果当前没有在处理中，直接开始处理",
    "                if self._task_queue_len() > 0:\n                    # 如果当前没有在处理中，直接开始处理",
    1,
)
t = t.replace(
    "                if self.task_queue:\n                    # 如果当前正在处理中，记录日志，等待当前批次完成后自动继续",
    "                if self._task_queue_len() > 0:\n                    # 如果当前正在处理中，记录日志，等待当前批次完成后自动继续",
    1,
)
p.write_text(t, encoding="utf-8")
print("fixes ok", count)
