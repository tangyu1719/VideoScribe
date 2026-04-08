# 清理web_api.py中的示例/MOCK数据

with open('web_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修复 process_video_task 中的示例数据
content = content.replace('task["title"] = "示例视频标题"', 'task["title"] = ""')
content = content.replace('task["transcript"] = "这是视频的转录内容示例..."', 'task["transcript"] = ""')
content = content.replace('task["summary"] = "这是AI分析的摘要内容..."', 'task["summary"] = ""')

# 2. 修复 send_message 中的示例回复
content = content.replace('"content": f"这是对\'{message.content}\'的回复示例..."', '"content": ""')

# 3. 修复 analyze_link 中的示例数据
content = content.replace('"title": "示例标题"', '"title": ""')
content = content.replace('"content": "示例内容..."', '"content": ""')
content = content.replace('"author": "作者名"', '"author": ""')
content = content.replace('"platform": "xiaohongshu"', '"platform": ""')
content = content.replace('"type": "image"', '"type": ""')

# 4. 修复 AI分析中的示例数据
content = content.replace('"summary": f"根据{\'自定义要求：\' + user_prompt if user_prompt else \'默认分析\'}，这是一个示例内容的AI分析摘要..."', '"summary": ""')
content = content.replace('"关键点1：示例要点"', '""')
content = content.replace('"关键点2：另一个要点"', '""')
content = content.replace('"关键点3：第三个要点"', '""')
content = content.replace('"示例", "测试", "AI分析"', '')

# 保存文件
with open('web_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('已清理所有示例数据')
