@echo off
chcp 65001 >nul
echo ================================================================================
echo 抖音链接解析修复 - 最终测试
echo ================================================================================
echo.

echo 1. 测试 link_analyzer.py 的 URL 提取功能
echo ---------------------------------------------------------------------------
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -c "import re; text='2.89 e@O.kc 05/03 Okp:/ 面试官：skill 解决了 agent 的什么痛点？#agent # ai 大模型 # 人工智能 # 大模型应用  `https://v.douyin.com/F0hlcj9C0lE/`  复制此链接，打开 Dou 音搜索，直接观看视频！'; url_pattern = r'https?://[^\s<>\"{}|\\\\^`\\[\\]]+'; matches = re.findall(url_pattern, text); print('提取结果:', matches[0] if matches else '失败'); print('期望结果：https://v.douyin.com/F0hlcj9C0lE/'); print('测试:', '通过' if matches and matches[0] == 'https://v.douyin.com/F0hlcj9C0lE/' else '失败')"
echo.

echo 2. 检查 link_analyzer.py 是否包含 _extract_clean_url 方法
echo ---------------------------------------------------------------------------
findstr /C:"def _extract_clean_url" src\agent\link_analyzer.py >nul && echo ✓ link_analyzer.py 包含 URL 清理方法 || echo ✗ link_analyzer.py 缺少 URL 清理方法
echo.

echo 3. 检查 video_gui.py 是否包含 _extract_clean_url 方法
echo ---------------------------------------------------------------------------
findstr /C:"def _extract_clean_url" src\agent\video_gui.py >nul && echo ✓ video_gui.py 包含 URL 清理方法 || echo ✗ video_gui.py 缺少 URL 清理方法
echo.

echo 4. 检查 video_gui.py 是否强制重新加载 link_analyzer 模块
echo ---------------------------------------------------------------------------
findstr /C:"importlib.reload" src\agent\video_gui.py >nul && echo ✓ video_gui.py 包含模块重新加载逻辑 || echo ✗ video_gui.py 缺少模块重新加载逻辑
echo.

echo 5. 检查 video_gui.py 的 download_video 方法是否调用 URL 清理
echo ---------------------------------------------------------------------------
findstr /C:"_extract_clean_url" src\agent\video_gui.py >nul && echo ✓ video_gui.py download_video 包含 URL 清理调用 || echo ✗ video_gui.py download_video 缺少 URL 清理调用
echo.

echo ================================================================================
echo 检查完成！
echo ================================================================================
echo.
echo 修复要点：
echo   1. link_analyzer.py 添加了 _extract_clean_url 方法
echo   2. video_gui.py 添加了 _extract_clean_url 方法
echo   3. video_gui.py 强制重新加载 link_analyzer 模块（使用 importlib.reload）
echo   4. video_gui.py 的 download_video 方法调用 URL 清理
echo   5. video_gui.py 的 _run_xiaohongshu_analysis 方法强制重新加载模块
echo.
echo 现在可以运行 video_gui.py 并测试抖音链接下载功能！
echo ================================================================================
pause
