import requests
from bs4 import BeautifulSoup
import re
import json

url = 'https://www.xiaohongshu.com/explore/6900d1c70000000007035e79?app_platform=android&ignoreEngage=true&app_version=9.19.4&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M=&author_share=1&xhsshare=&shareRedId=ODZGQzVKNz02NzUyOTgwNjY0OTc8RjdP&apptime=1771134517&share_id=cf150dbd16f94855950aa3d742a6f7fd&share_channel=wechat'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'Referer': 'https://www.xiaohongshu.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

try:
    print('正在访问小红书链接...')
    r = requests.get(url, headers=headers, timeout=15)
    print(f'状态码: {r.status_code}')
    
    if r.status_code == 200:
        print('\n--- 页面内容提取 ---')
        
        # 提取标题
        title_match = re.search(r'<title>(.*?)</title>', r.text)
        if title_match:
            print(f'标题: {title_match.group(1)}')
        
        # 尝试从script标签提取JSON数据（小红书常用方式）
        print('\n--- 尝试提取JSON数据 ---')
        script_pattern = re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', re.DOTALL)
        match = script_pattern.search(r.text)
        
        if match:
            try:
                json_data = json.loads(match.group(1))
                print('成功提取JSON数据')
                # 打印JSON结构
                print(json.dumps(json_data, indent=2, ensure_ascii=False)[:1000] + '...')
            except json.JSONDecodeError:
                print('JSON解析失败')
        
        # 尝试另一种常见的JSON存储方式
        note_pattern = re.compile(r'window\.note\s*=\s*({.*?});', re.DOTALL)
        match = note_pattern.search(r.text)
        
        if match:
            try:
                note_data = json.loads(match.group(1))
                print('\n成功提取note数据')
                print(json.dumps(note_data, indent=2, ensure_ascii=False)[:1000] + '...')
            except json.JSONDecodeError:
                print('note JSON解析失败')
        
        # 提取图片
        print('\n--- 图片链接 ---')
        soup = BeautifulSoup(r.text, 'html.parser')
        img_tags = soup.find_all('img')
        img_links = []
        for img in img_tags:
            src = img.get('src')
            if src and ('http' in src):
                img_links.append(src)
                print(src)
        
        # 提取文本内容
        print('\n--- 文本内容 ---')
        # 查找可能包含内容的div
        content_divs = soup.find_all('div', class_=re.compile(r'content|text|desc|note', re.I))
        text_content = []
        for div in content_divs:
            text = div.get_text(strip=True)
            if text and len(text) > 20:
                text_content.append(text)
                print(text[:200] + ('...' if len(text) > 200 else ''))
        
        print('\n--- 提取完成 ---')
        print(f'提取到 {len(text_content)} 段文本')
        print(f'提取到 {len(img_links)} 张图片')
        
    else:
        print(f'访问失败，状态码: {r.status_code}')
        print('响应头:', dict(r.headers))
        print('响应内容前500字符:', r.text[:500])
        
except Exception as e:
    print(f'发生错误: {e}')
    import traceback
    traceback.print_exc()
