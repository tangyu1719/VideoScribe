import os

def resolve_ffmpeg_bin_dir():
    """优先 demo_wendanghua/ffmpeg/bin；src/agent 下向上三级；最后 tools/ffmpeg/bin。"""
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.normpath(os.path.join(base, "ffmpeg", "bin")),
        os.path.normpath(os.path.join(base, "..", "..", "..", "ffmpeg", "bin")),
        os.path.normpath(os.path.join(base, "tools", "ffmpeg", "bin")),
    ]
    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        if os.path.isfile(os.path.join(c, "ffmpeg.exe")):
            return c
    return None


def ensure_ffmpeg_path():
    """把找到的 ffmpeg bin 放到 PATH 最前；返回 bin 目录或 None。"""
    d = resolve_ffmpeg_bin_dir()
    if d:
        sep = os.pathsep
        cur = os.environ.get("PATH", "")
        if cur.startswith(d + sep) or cur == d or (sep + d + sep) in (sep + cur + sep):
            pass
        else:
            os.environ["PATH"] = d + sep + cur
    return d
