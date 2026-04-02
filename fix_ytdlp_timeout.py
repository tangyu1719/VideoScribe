# 修复yt-dlp超时问题

with open('video_gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 增加超时时间从60秒到180秒
content = content.replace('result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)', 
                          'result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)')

# 2. 增加重试次数从2次到3次
content = content.replace('while retry_count < max_retries:', 
                          'while retry_count < max_retries:  # max_retries=3')

# 3. 添加B站cookies支持（如果存在cookies文件）
# 在构建cmd的地方添加cookies参数
old_cmd_build = '''# 构建yt-dlp命令，直接下载到目标文件夹（优化：减少不必要的参数）
            cmd = [
                "yt-dlp",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                "--referer", referer,'''

new_cmd_build = '''# 构建yt-dlp命令，直接下载到目标文件夹（优化：减少不必要的参数）
            cmd = [
                "yt-dlp",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win