from requests_html import HTMLSession
import re
import json

url = 'https://www.xiaohongshu.com/explore/6900d1c70000000007035e79?app_platform=android&ignoreEngage=true&app_version=9.19.4&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M=&author_share=1&xhsshare=&shareRedId=ODZGQzVKNz02NzUyOTgwNjY0OTc8RjdP&apptime=1771134517&share_id=cf150dbd16f94855950aa3d742a6f7fd&share_channel=wechat'

try:
    print('正在访问小红书链接（支持JavaScript渲染）...')
    session = HTMLSession()
    r = session.get(url)
    
    # 渲染JavaScript
    print('正在渲染页面...')
    r.html.render(timeout=30, sleep=5)
    
    print(f'状态码: {r.status_code}')
    
    if r.status_code == 200:
        print('\n--- 页面内容提取 ---')
        
        # 提取标题
        title = r.html.find('title', first=True)
        if title:
            print(f'标题: {title.text}')
        
        # 提取图片
        print('\n--- 图片链接 ---')
        img_elements = r.html.find('img')
        img_links = []
        for img in img_elements:
            src = img.attrs.get('src')
            if src and ('http' in src):
                img_links.append(src)
                print(src)
        
        # 提取文本内容
        print('\n--- 文本内容 ---')
        # 查找可能包含内容的元素
        content_elements = r.html.find('div', containing='算法岗常考手撕合集')
        text_content = []
        for elem in content_elements:
            text = elem.text.strip()
            if text and len(text) > 20:
                text_content.append(text)
                print(text[:300] + ('...' if len(text) > 300 else ''))
        
        # 尝试从script标签提取JSON数据
        print('\n--- 尝试提取JSON数据 ---')
        script_elements = r.html.find('script')
        for script in script_elements:
            script_text = script.text
            if '__INITIAL_STATE__' in script_text:
                print('找到INITIAL_STATE数据')
                # 提取JSON部分
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_text, re.DOTALL)
                if match:
                    try:
                        json_data = json.loads(match.group(1))
                        print('成功解析JSON数据')
                        # 打印前500个字符
                        print(json.dumps(json_data, indent=2, ensure_ascii=False)[:500] + '...')
                    except json.JSONDecodeError:
                        print('JSON解析失败')
                break
        
        # 查找包含算法内容的元素
        print('\n--- 查找算法相关内容 ---')
        algorithm_elements = r.html.find('div', containing=['算法', '面试', '手撕'])
        for elem in algorithm_elements:
            text = elem.text.strip()
            if text and len(text) > 50:
                print('\n算法相关内容:')
                print(text[:400] + ('...' if len(text) > 400 else ''))
        
        print('\n--- 提取完成 ---')
        print(f'提取到 {len(text_content)} 段文本')
        print(f'提取到 {len(img_links)} 张图片')
        
    else:
        print(f'访问失败，状态码: {r.status_code}')
        
except Exception as e:
    print(f'发生错误: {e}')
    import traceback
    traceback.print_exc()
finally:
    session.close()
