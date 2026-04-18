import requests
from bs4 import BeautifulSoup
import re
import json

# 测试小红书链接
url = 'https://www.xiaohongshu.com/explore/6900d1c70000000007035e79?app_platform=android&ignoreEngage=true&app_version=9.19.4&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M=&author_share=1&xhsshare=&shareRedId=ODZGQzVKNz02NzUyOTgwNjY0OTc8RjdP&apptime=1771134517&share_id=cf150dbd16f94855950aa3d742a6f7fd&share_channel=wechat'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
    'Referer': 'https://www.xiaohongshu.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

print(f"访问链接: {url}")
response = requests.get(url, headers=headers, timeout=15)
print(f"状态码: {response.status_code}")

# 保存HTML内容到文件，方便查看
with open('xiaohongshu_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("HTML内容已保存到 xiaohongshu_page.html")

# 查找__INITIAL_STATE__
if '__INITIAL_STATE__' in response.text:
    print("\n找到 __INITIAL_STATE__")
    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', response.text, re.DOTALL)
    if match:
        print("成功匹配到 JSON 数据")
        try:
            json_data = json.loads(match.group(1))
            print(f"JSON 数据键: {list(json_data.keys())}")
            
            # 查找图片链接
            if 'note' in json_data and 'noteDetailMap' in json_data['note']:
                print("\n找到 noteDetailMap")
                for note_id, note_data in json_data['note']['noteDetailMap'].items():
                    print(f"\n笔记ID: {note_id}")
                    if 'note' in note_data:
                        note = note_data['note']
                        print(f"笔记键: {list(note.keys())}")
                        
                        if 'imageList' in note:
                            image_list = note['imageList']
                            print(f"\n找到 {len(image_list)} 张图片:")
                            for i, img in enumerate(image_list):
                                print(f"  图片 {i+1}: {img.get('urlDefault', '无urlDefault')}")
                        else:
                            print("未找到 imageList")
            else:
                print("未找到 noteDetailMap")
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
    else:
        print("未匹配到 JSON 数据")
else:
    print("\n未找到 __INITIAL_STATE__")

# 直接从HTML查找图片
soup = BeautifulSoup(response.text, 'html.parser')
img_tags = soup.find_all('img')
print(f"\n\nHTML中共有 {len(img_tags)} 个 img 标签")
for i, img in enumerate(img_tags[:10]):  # 只显示前10个
    src = img.get('src')
    if src:
        print(f"  img {i+1}: {src[:100]}...")
