from pathlib import Path
p = Path(r"F:\java\AIOPS\SuperBizAgent-release-2026-01-02\demo_wendanghua\SuperBizAgent-AgentFramework\src\agent\video_gui.py")
lines = p.read_text(encoding="utf-8").splitlines(True)
start = None
for i, line in enumerate(lines):
    if "线程池滑动窗口" in line and line.lstrip().startswith("#"):
        start = i
        break
if start is None:
    raise SystemExit("start marker not found")
end = None
for i in range(start + 1, len(lines)):
    if lines[i].startswith("    def stop_task"):
        end = i
        break
if end is None:
    raise SystemExit("stop_task marker not found")
for i in range(start, end):
    if lines[i].strip():
        lines[i] = "    " + lines[i]
p.write_text("".join(lines), encoding="utf-8")
print("indented", start + 1, "to", end)
