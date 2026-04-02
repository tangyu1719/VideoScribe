#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章完整处理测试
- 提取文章内容
- 下载图片并OCR
- AI分析生成摘要
- 输出完整Markdown文档
"""

import os
import sys
import time
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wechat_article_processor import WeChatArticleProcessor

# 火山引擎API配置
VOLCENGINE_API_KEY = "5da00752-8f46-44eb-b162-5c52f2a249b3"
VOLCENGINE_API_URL = "https://ark.cn-beijing.volces.com/api/v3"

def summarize_with_volcengine(text, user_prompt=""):
    """使用火山引擎API进行文本总结"""
    try:
        from volcenginesdkarkruntime import Ark
        
        system_prompt = """你是一个专业的文章分析助手，擅长从文章内容中提取关键信息并进行结构化分析。
你的输出格式要求：
1. 第一行是简洁的中文标题（不超过20字符，不要包含#号，不要包含markdown语法标记）
2. 后续是结构化的分析内容"""
        
        summary_prompt = """请对以下文章进行深度分析，提取关键知识点，整理成结构化的格式。

要求：
1. 第一行必须是一个简洁的中文标题（不超过20个字符，不要包含#号）
2. 提供内容概览（简要说明文章主题和核心观点）
3. 提取核心要点（用 bullet points 列出3-5个关键知识点）
4. 详细分析（对文章主要内容进行结构化梳理）
5. 总结（用2-3句话总结文章价值）

文章内容：
{text}"""
        
        # 构建请求输入
        input_content = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"{system_prompt}\n\n{summary_prompt.format(text=text)}"
                    }
                ],
            }
        ]
        
        # 创建Ark客户端
        client = Ark(
            base_url=VOLCENGINE_API_URL,
            api_key=VOLCENGINE_API_KEY,
        )
        
        print("调用火山引擎API进行文章分析...")
        # 发送请求 - 使用 Doubao-Seed-2.0-Code 模型
        response = client.responses.create(
            model="Doubao-Seed-2.0-Code",
            input=input_content
        )
        
        # 解析响应
        if response.status == "completed" and response.output:
            for item in response.output:
                if item.type == "message" and item.role == "assistant":
                    for content in item.content:
                        if content.type == "output_text":
                            summary = content.text
                            if summary:
                                print("火山引擎API调用成功")
                                return summary
        
        print("火山引擎API返回空结果或格式不正确")
        return None
        
    except Exception as e:
        print(f"火山引擎API调用异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_title_from_summary(summary):
    """从AI分析结果中提取标题"""
    if not summary:
        return "未知标题"
    
    lines = summary.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 如果是Markdown标题格式 (# 标题)，提取#后面的内容
        if line.startswith('#'):
            title = line.lstrip('#').strip()
            if title and len(title) > 3:
                import re
                title = re.sub(r'[\\/:*?"<>|]', '', title)
                title = title[:20].strip()
                title = title.replace(' ', '_')
                if title:
                    return title
        else:
            # 普通文本行，跳过太短的内容
            if len(line) > 3 and len(line) <= 50:
                import re
                title = re.sub(r'[\\/:*?"<>|]', '', line)
                title = title[:20].strip()
                title = title.replace(' ', '_')
                if title:
                    return title
    
    return "未知标题"

def generate_markdown(article_data, ai_summary, output_dir="output"):
    """生成完整的Markdown文档"""
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取当前日期
    current_date = time.strftime('%m-%d')
    datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 从AI分析中提取标题
    title = extract_title_from_summary(ai_summary)
    if title == "未知标题":
        title = article_data.get('title', '微信公众号文章分析')
        import re
        title = re.sub(r'[\\/:*?"<>|]', '', title)
        title = title.replace(' ', '_')
    
    # 获取现有文件数量
    existing_md = [f for f in os.listdir(output_dir) if f.endswith('.md')]
    total_count = len(existing_md) + 1
    
    # 生成文件名
    md_path = os.path.join(output_dir, f"{total_count:03d}-{current_date}-{title}_内容分析.md")
    
    # 构建Markdown内容
    author = article_data.get('author', '')
    publish_time = article_data.get('publish_time', '')
    content = article_data.get('content', '')
    url = article_data.get('url', '')
    image_count = article_data.get('image_count', 0)
    image_analysis = article_data.get('image_analysis', [])
    
    md_content = f"""# {article_data.get('title', '未命名')}

**作者**: {author if author else '未知'}
**发布时间**: {publish_time if publish_time else '未知'}
**原文链接**: {url}

---

## 正文内容

{content[:8000] if len(content) > 8000 else content}

"""
    
    if len(content) > 8000:
        md_content += "\n...（内容过长，已截断）\n\n"
    
    # 添加图片OCR内容
    if image_analysis:
        md_content += "## 图片中的文字内容\n\n"
        for i, img in enumerate(image_analysis):
            if img.get('text'):
                md_content += f"### 图片 {i+1}\n"
                md_content += f"![图片{i+1}]({img.get('local_path', '')})\n\n"
                md_content += f"**OCR识别内容**:\n```\n{img['text']}\n```\n\n"
    
    # 添加图片统计
    md_content += f"""## 图片统计
- 图片数量: {image_count}
- OCR识别: {len([img for img in image_analysis if img.get('text')])}/{len(image_analysis)} 张

---

## AI分析摘要

{ai_summary}

---

*分析时间: {datetime_str}*
*由视频转文字处理工具自动生成*
"""
    
    # 写入文件
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return md_path

def main():
    """主函数"""
    test_url = 'https://mp.weixin.qq.com/s/7uMyf62I3FQi3UpMoEYvmg'
    
    print("=" * 60)
    print("微信公众号文章完整处理测试")
    print("=" * 60)
    print(f"目标链接: {test_url}")
    print()
    
    # 步骤1: 提取文章内容
    print("【步骤1】提取文章内容...")
    processor = WeChatArticleProcessor()
    article_data = processor.extract_article(test_url)
    
    if 'error' in article_data:
        print(f"错误: {article_data['error']}")
        return
    
    print(f"✓ 标题: {article_data['title']}")
    print(f"✓ 作者: {article_data['author']}")
    print(f"✓ 发布时间: {article_data['publish_time']}")
    print(f"✓ 图片数量: {article_data['image_count']}")
    print(f"✓ 正文长度: {len(article_data['content'])} 字符")
    print()
    
    # 步骤2: 生成摘要
    print("【步骤2】生成文章摘要...")
    summary = processor.generate_summary(article_data)
    print(f"✓ 摘要长度: {len(summary)} 字符")
    print()
    
    # 步骤3: AI分析
    print("【步骤3】AI智能分析...")
    ai_summary = summarize_with_volcengine(summary)
    
    if not ai_summary:
        print("✗ AI分析失败")
        return
    
    print("✓ AI分析完成")
    print()
    
    # 步骤4: 生成Markdown文档
    print("【步骤4】生成Markdown文档...")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    md_path = generate_markdown(article_data, ai_summary, output_dir)
    print(f"✓ Markdown文档已生成: {md_path}")
    print()
    
    # 输出AI分析结果预览
    print("=" * 60)
    print("AI分析结果预览:")
    print("=" * 60)
    print(ai_summary[:1000] + "..." if len(ai_summary) > 1000 else ai_summary)
    print()
    
    print("=" * 60)
    print("处理完成!")
    print(f"完整文档: {md_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
