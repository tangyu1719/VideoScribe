from pathlib import Path
p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py")
t = p.read_text(encoding="utf-8")

# 1) Add lock after active_instance_count
old1 = "        self.active_instance_count = 0  # 当前活跃实例数\n        \n        # 功能开关"
new1 = "        self.active_instance_count = 0  # 当前活跃实例数\n        self._whisper_transcribe_lock = threading.Lock()  # openai-whisper 的 transcribe 非线程安全，必须串行\n        \n        # 功能开关"
if old1 not in t:
    raise SystemExit("lock anchor missing")
t = t.replace(old1, new1, 1)

# 2) Insert ffprobe helper before Whisper pool section
marker = "    # ==================== Whisper 实例池管理 ====================\n    def _get_whisper_instance(self):"
helper = '''    def _ffprobe_audio_duration_sec(self, media_path: str):
        """检测首个音轨时长（秒）。无 ffprobe、无音轨或失败时返回 None（不阻断，由 Whisper 再试）。"""
        import subprocess
        import shutil
        if not shutil.which("ffprobe"):
            return None
        try:
            r = subprocess.run(
                [
                    "ffprobe", "-v", "error", "-select_streams", "a:0",
                    "-show_entries", "stream=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    media_path,
                ],
                capture_output=True,
                text=True,
                timeout=90,
            )
            out = (r.stdout or "").strip()
            if r.returncode != 0 or not out:
                return 0.0
            return float(out.split()[0])
        except (ValueError, subprocess.TimeoutExpired, OSError, IndexError):
            return None

    # ==================== Whisper 实例池管理 ====================
    def _get_whisper_instance(self):'''

if marker not in t:
    raise SystemExit("marker missing")
t = t.replace(marker, helper, 1)

# 3) Replace _get_whisper_instance body - from docstring through raise RuntimeError at end of lock block
import re
pat = r'(    def _get_whisper_instance\(self\):\n        """\n        获取 Whisper 模型实例\n)(.*?)(        with self\.whisper_instance_lock:\n)(.*?)(\n    def _release_whisper_instance)'

def repl(m):
    head = m.group(1)
    g3 = m.group(3)
    tail = m.group(5)
    new_body = '''        \"\"\"获取 Whisper 模型实例（与 speech_to_text 预加载的 model_cache 一致）。
        说明：多线程并发时 transcribe 必须串行（见 _whisper_transcribe_lock），
        实例池不能修复「无音轨/空音频」类错误；此类错误应看 ffprobe 与文件本身。
        \"\"\"\n'''
    new_lock = g3 + """            if self.model_cache:
                return "main", self.model_cache
            raise RuntimeError("无法获取 Whisper 实例（请先加载 model_cache）")\n"""
    return head + new_body + new_lock + tail

t2, n = re.subn(pat, repl, t, count=1, flags=re.DOTALL)
if n != 1:
    raise SystemExit(f"get_whisper replace failed n={n}")
t = t2

# 4) Wrap transcribe in _manage_whisper_queue
old4 = """                transcribe_start = time.time()
                result = model.transcribe(
                    video_file,"""
new4 = """                transcribe_start = time.time()
                with self._whisper_transcribe_lock:
                    result = model.transcribe(
                    video_file,"""
if old4 not in t:
    raise SystemExit("manage transcribe anchor missing")
t = t.replace(old4, new4, 1)
# fix indent of following lines - transcribe args need extra 4 spaces
# model.transcribe block - the closing paren for transcribe - find and add close for with

old5 = """                    compression_ratio_threshold=2.4  # 设置压缩比阈值，过滤低质量转写
                )
                
                transcribe_end = time.time()
                self.append_log(f"转写耗时：{transcribe_end - transcribe_start:.2f}秒", "INFO")"""

new5 = """                    compression_ratio_threshold=2.4  # 设置压缩比阈值，过滤低质量转写
                    )
                
                transcribe_end = time.time()
                self.append_log(f"转写耗时：{transcribe_end - transcribe_start:.2f}秒", "INFO")"""

if old5 not in t:
    raise SystemExit("manage transcribe close missing")
t = t.replace(old5, new5, 1)

# Indent inner lines of transcribe inside with - they need one more level
# The replace above only added with and opened transcribe - inner args still 16 spaces, need 20
# Actually Python allows if consistent - transcribe( has args at wrong indent - syntax error

