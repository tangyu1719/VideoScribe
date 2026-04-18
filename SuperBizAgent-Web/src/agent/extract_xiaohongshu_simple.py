import requests
from bs4 import BeautifulSoup
import re

url = 'https://www.xiaohongshu.com/explore/6900d1c70000000007035e79?app_platform=android&ignoreEngage=true&app_version=9.19.4&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M=&author_share=1&xhsshare=&shareRedId=ODZGQzVKNz02NzUyOTgwNjY0OTc8RjdP&apptime=1771134517&share_id=cf150dbd16f94855950aa3d742a6f7fd&share_channel=wechat'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'Referer': 'https://www.xiaohongshu.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cookie': 'xsecappid=xhs-pc-web; a1=198c73827b3fvrg0ilz7c68qz34e9t1d913uc7c040000301616; webId=8d2a9b483a0c4a95b3e88a9e8a8a8a8a; gid=yYDPyjYq4DkMyYDPyjYqO8B2uFj1Y4tKX8qWZJ1Iu48q28qWJ1Iu48q2; gsessionid=8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; webBuild=4.83.0; acw_tc=0a00dddd17711345178a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; web_session=0400c7d3df3e255b1a9c6b2a1a9c6b2a1a9c6b2a1a9c6b2a1a9c6b2a1a9c6b2a; sec_poison_id=8a8a8a8a-8a8a-4a8a-8a8a-8a8a8a8a8a8a; gftoken=8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; websectiga=8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; tt_webid=8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; passport_csrf_token=8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; passport_csrf_token_default=8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a; xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M='
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
        
        # 解析HTML
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 提取图片
        print('\n--- 图片链接 ---')
        img_tags = soup.find_all('img')
        img_links = []
        for img in img_tags:
            src = img.get('src')
            if src and ('http' in src) and not ('gif' in src):
                img_links.append(src)
                print(src)
        
        # 提取文本内容
        print('\n--- 文本内容 ---')
        
        # 查找包含算法内容的元素
        text_content = []
        
        # 方法1：查找所有div元素，过滤包含关键词的
        divs = soup.find_all('div')
        for div in divs:
            text = div.get_text(strip=True)
            if text and len(text) > 50 and ('算法岗' in text or '常考手撕' in text or '面试' in text):
                text_content.append(text)
                print(f'内容片段: {text[:300]}...')
        
        # 方法2：查找所有p元素
        print('\n--- 段落内容 ---')
        p_tags = soup.find_all('p')
        for p in p_tags:
            text = p.get_text(strip=True)
            if text and len(text) > 30 and ('算法' in text or '面试' in text or '手撕' in text):
                print(f'段落: {text}')
        
        # 方法3：查找script标签中的JSON数据
        print('\n--- 尝试提取JSON数据 ---')
        script_tags = soup.find_all('script')
        for script in script_tags:
            script_text = script.get_text()
            if '算法岗常考手撕合集' in script_text:
                print('找到包含算法内容的script标签')
                # 提取相关内容
                lines = script_text.split('\n')
                for line in lines:
                    if '算法岗常考手撕合集' in line or '面试' in line or '算法' in line:
                        print(line.strip())
        
        # 提取可能的表格数据
        print('\n--- 尝试提取表格数据 ---')
        tables = soup.find_all('table')
        for table in tables:
            print('找到表格:')
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_text = [cell.get_text(strip=True) for cell in cells]
                print(row_text)
        
        print('\n--- 提取完成 ---')
        print(f'提取到 {len(text_content)} 段相关文本')
        print(f'提取到 {len(img_links)} 张图片')
        
    else:
        print(f'访问失败，状态码: {r.status_code}')
        print('响应内容前1000字符:', r.text[:1000])
        
except Exception as e:
    print(f'发生错误: {e}')
    import traceback
    traceback.print_exc()
