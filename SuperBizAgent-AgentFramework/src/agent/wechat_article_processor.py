#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章处理器
- 提取文章标题、作者、发布时间、正文内容
- 下载文章中的图片
- 对图片进行OCR识别
- 生成结构化Markdown文档
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
import html
import time
from urllib.parse import urljoin, urlparse
from aip import AipOcr

class WeChatArticleProcessor:
    """微信公众号文章处理器"""
    
    def __init__(self):
        # 百度OCR API配置
        self.APP_ID = '122094788'
        self.API_KEY = 'KZOpVw7PGLRiBdsqRnuLFVY7'
        self.SECRET_KEY = 'L1pdbtb4IZZv67ofXnsxDNAhELGN2UXs'
        
        # 初始化AipOcr
        self.client = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        
        # 请求头配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://mp.weixin.qq.com/'
        }
        
        # 创建图片保存目录
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.path.join(self.base_dir, 'wechat_images')
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
    
    def is_wechat_url(self, url):
        """判断是否为微信公众号文章链接"""
        return 'mp.weixin.qq.com' in url.lower()
    
    def download_image(self, url, article_id):
        """下载图片并保存到本地"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                # 从URL中提取文件扩展名
                parsed_url = urlparse(url)
                path = parsed_url.path
                ext = os.path.splitext(path)[1]
                if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    ext = '.jpg'
                
                # 生成文件名
                filename = f"{article_id}_{int(time.time() * 1000)}{ext}"
                filepath = os.path.join(self.images_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                return {
                    'url': url,
                    'local_path': filepath,
                    'filename': filename
                }
            else:
                print(f"下载图片失败: {response.status_code} - {url}")
                return None
        except Exception as e:
            print(f"下载图片出错: {e} - {url}")
            return None
    
    def ocr_image(self, image_data, max_retries=3):
        """使用百度OCR识别图片文字，带重试机制"""
        for attempt in range(max_retries):
            try:
                # 调用通用文字识别（高精度版）
                result = self.client.basicAccurate(image_data)
                
                # 检查是否触发QPS限制
                if result and 'error_code' in result and result['error_code'] == 18:
                    print(f"  触发QPS限制，等待后重试 ({attempt+1}/{max_retries})...")
                    time.sleep(1.5)
                    continue
                
                return result
            except Exception as e:
                print(f"OCR识别出错 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None
        
        return None
    
    def ocr_image_file(self, image_path, max_retries=3):
        """对本地图片文件进行OCR识别"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return self.ocr_image(image_data, max_retries)
        except Exception as e:
            print(f"读取图片文件出错: {e}")
            return None
    
    def extract_text_from_ocr(self, result):
        """从OCR结果中提取文本"""
        if not result or 'words_result' not in result:
            return ""
        
        text = ""
        for item in result['words_result']:
            text += item['words'] + '\n'
        
        return text.strip()
    
    def extract_article(self, url):
        """
        提取微信公众号文章内容
        
        Returns:
            dict: 包含文章信息的字典
        """
        # 清理URL（去除末尾的非法字符）
        url = url.strip().rstrip('|').rstrip('.').rstrip(',').rstrip(';')
        
        if not self.is_wechat_url(url):
            return {'error': '不是有效的微信公众号文章链接'}
        
        try:
            print(f"正在访问微信公众号文章: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return {
                    'error': f'访问失败，状态码: {response.status_code}',
                    'url': url
                }
            
            # 检查是否是错误页面
            if '参数错误' in response.text or 'param error' in response.text.lower():
                return {
                    'error': '链接无效或已过期（参数错误）',
                    'url': url
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章ID（用于图片命名）
            article_id = hash(url) % 10000000
            
            # 提取标题
            title_elem = soup.find('h1', class_='rich_media_title') or \
                        soup.find('h2', class_='rich_media_title')
            title = title_elem.get_text(strip=True) if title_elem else "未找到标题"
            
            # 提取作者
            author_elem = soup.find('a', id='js_name') or \
                         soup.find('span', class_='profile_nickname')
            author = author_elem.get_text(strip=True) if author_elem else "未找到作者"
            
            # 提取发布时间
            time_elem = soup.find('em', id='publish_time')
            publish_time = time_elem.get_text(strip=True) if time_elem else "未找到发布时间"
            
            # 提取正文内容
            content_elem = soup.find('div', id='js_content')
            content = ""
            image_links = []
            downloaded_images = []
            
            if content_elem:
                # 清理script和style标签
                for script in content_elem.find_all(['script', 'style']):
                    script.decompose()
                
                # 提取图片链接
                img_tags = content_elem.find_all('img')
                for img in img_tags:
                    # 尝试获取图片URL（可能是data-src或src）
                    img_url = img.get('data-src') or img.get('src')
                    if img_url and ('mmbiz.qpic.cn' in img_url or 'mmbizurl.cn' in img_url):
                        image_links.append(img_url)
                        
                        # 下载图片
                        img_info = self.download_image(img_url, article_id)
                        if img_info:
                            downloaded_images.append(img_info)
                
                # 提取文本内容
                # 保留段落结构
                paragraphs = []
                for elem in content_elem.find_all(['p', 'section', 'span']):
                    text = elem.get_text(strip=True)
                    if text and len(text) > 0:
                        paragraphs.append(text)
                
                # 去重并合并
                seen = set()
                unique_paragraphs = []
                for p in paragraphs:
                    if p not in seen and len(p) > 5:
                        seen.add(p)
                        unique_paragraphs.append(p)
                
                content = '\n\n'.join(unique_paragraphs)
                content = html.unescape(content)
            else:
                content = "未找到正文内容"
            
            # 对下载的图片进行OCR识别
            print(f"开始OCR识别 {len(downloaded_images)} 张图片...")
            image_analysis = []
            for i, img_info in enumerate(downloaded_images):
                print(f"OCR识别图片 {i+1}/{len(downloaded_images)}: {img_info['filename']}")
                ocr_result = self.ocr_image_file(img_info['local_path'])
                if ocr_result:
                    img_text = self.extract_text_from_ocr(ocr_result)
                    image_analysis.append({
                        'url': img_info['url'],
                        'local_path': img_info['local_path'],
                        'filename': img_info['filename'],
                        'text': img_text
                    })
                
                # 添加延时，避免触发百度OCR的QPS限制
                if i < len(downloaded_images) - 1:
                    time.sleep(1.0)
            
            return {
                'title': title,
                'author': author,
                'publish_time': publish_time,
                'content': content,
                'url': url,
                'image_count': len(image_links),
                'image_links': image_links,
                'downloaded_images': downloaded_images,
                'image_analysis': image_analysis
            }
            
        except Exception as e:
            print(f"提取文章出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'url': url
            }
    
    def generate_summary(self, article_data):
        """生成文章摘要（用于AI分析前的预处理）"""
        title = article_data.get('title', '未命名')
        author = article_data.get('author', '未知作者')
        publish_time = article_data.get('publish_time', '')
        content = article_data.get('content', '')
        image_analysis = article_data.get('image_analysis', [])
        
        summary = f"# {title}\n\n"
        summary += f"**作者**: {author}\n"
        if publish_time:
            summary += f"**发布时间**: {publish_time}\n"
        summary += "\n"
        
        # 添加正文内容
        if content:
            summary += "## 正文内容\n\n"
            # 限制内容长度，避免超出AI处理限制
            if len(content) > 8000:
                summary += content[:8000] + "\n\n...（内容过长，已截断）"
            else:
                summary += content
            summary += "\n\n"
        
        # 添加图片OCR内容
        if image_analysis:
            summary += "## 图片中的文字内容\n\n"
            for i, img in enumerate(image_analysis):
                if img.get('text'):
                    summary += f"### 图片 {i+1}\n"
                    summary += img['text'] + "\n\n"
        
        return summary


# 测试函数
if __name__ == "__main__":
    processor = WeChatArticleProcessor()
    
    # 测试链接
    test_url = 'https://mp.weixin.qq.com/s/7uMyf62I3FQi3UpMoEYvmg'
    
    result = processor.extract_article(test_url)
    
    if 'error' in result:
        print(f"错误: {result['error']}")
    else:
        print("=" * 50)
        print(f"标题: {result['title']}")
        print(f"作者: {result['author']}")
        print(f"发布时间: {result['publish_time']}")
        print(f"图片数量: {result['image_count']}")
        print("=" * 50)
        print("\n正文预览:")
        print(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
        
        # 生成摘要
        summary = processor.generate_summary(result)
        print("\n" + "=" * 50)
        print("生成的摘要:")
        print(summary[:1000] + "..." if len(summary) > 1000 else summary)
