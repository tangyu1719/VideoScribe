from bs4 import BeautifulSoup

# 读取HTML文件
with open('xiaohongshu_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 方法1：查找所有meta标签
print("方法1：查找所有meta标签")
meta_tags = soup.find_all('meta')
print(f"找到 {len(meta_tags)} 个meta标签")

# 方法2：查找property为og:image的meta标签
print("\n方法2：查找property为og:image的meta标签")
meta_og_images = soup.find_all('meta', property='og:image')
print(f"找到 {len(meta_og_images)} 个og:image meta标签")
for i, meta in enumerate(meta_og_images):
    print(f"  {i+1}: {meta.get('content', '无content')}")

# 方法3：查找name为og:image的meta标签
print("\n方法3：查找name为og:image的meta标签")
meta_name_images = soup.find_all('meta', attrs={'name': 'og:image'})
print(f"找到 {len(meta_name_images)} 个name=og:image meta标签")
for i, meta in enumerate(meta_name_images):
    print(f"  {i+1}: {meta.get('content', '无content')}")

# 方法4：使用正则表达式查找
print("\n方法4：使用正则表达式查找")
import re
matches = re.findall(r'<meta[^>]*og:image[^>]*content="([^"]*)"', html)
print(f"找到 {len(matches)} 个匹配")
for i, match in enumerate(matches):
    print(f"  {i+1}: {match}")
