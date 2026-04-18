from aip import AipOcr
import requests
import re
import json
from bs4 import BeautifulSoup
import os
import sys

# 添加当前目录到路径，以便导入 video_gui 中的函数
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class LinkAnalyzer:
    def __init__(self):
        # 百度 OCR API 配置
        self.APP_ID = '122094788'
        self.API_KEY = 'KZOpVw7PGLRiBdsqRnuLFVY7'
        self.SECRET_KEY = 'L1pdbtb4IZZv67ofXnsxDNAhELGN2UXs'
        
        # 初始化 AipOcr
        self.client = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        
        # 请求头配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
    
    def download_image(self, url):
        """下载图片并返回二进制数据"""
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.content
            else:
                print(f"下载图片失败：{response.status_code}")
                return None
        except Exception as e:
            print(f"下载图片出错：{e}")
            return None
    
    def ocr_image(self, image_data, max_retries=3):
        """使用百度 OCR 识别图片文字，带重试机制"""
        import time
        
        for attempt in range(max_retries):
            try:
                # 调用通用文字识别（高精度版）
                result = self.client.basicAccurate(image_data)
                
                # 检查是否触发 QPS 限制
                if result and 'error_code' in result and result['error_code'] == 18:
                    print(f"  触发 QPS 限制，等待后重试 ({attempt+1}/{max_retries})...")
                    time.sleep(1.5)  # 等待 1.5 秒后重试
                    continue
                
                return result
            except Exception as e:
                print(f"OCR 识别出错 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None
        
        return None
    
    def extract_text_from_ocr(self, result):
        """从 OCR 结果中提取文本"""
        if not result or 'words_result' not in result:
            return ""
        
        text = ""
        for item in result['words_result']:
            text += item['words'] + '\n'
        
        return text
    
    def analyze_link(self, url):
        """分析链接内容，判断类型并提取信息"""
        print(f"分析链接：{url}")
        
        # 1. 判断链接类型
        link_type = self._judge_link_type(url)
        print(f"链接类型：{link_type}")
        
        # 2. 根据类型分析内容
        if link_type == 'video':
            # 视频链接，返回视频分析结果
            return self._analyze_video(url)
        elif link_type == 'xiaohongshu':
            # 小红书链接，分析图片和文本
            return self._analyze_xiaohongshu(url)
        elif link_type == 'douyin_image':
            # 抖音图文链接，分析图片和文本
            return self._analyze_douyin_image(url)
        else:
            # 其他链接，尝试通用分析
            return self._analyze_general(url)
    
    def _judge_link_type(self, url):
        """判断链接类型"""
        if 'xiaohongshu.com' in url:
            return 'xiaohongshu'
        elif 'douyin.com' in url or 'tiktok.com' in url:
            # 抖音链接需要进一步判断是视频还是图文
            return self._detect_douyin_type(url)
        elif 'v.qq.com' in url or 'youku.com' in url or 'iqiyi.com' in url:
            return 'video'
        else:
            return 'general'
    
    def _detect_douyin_type(self, url):
        """检测抖音链接是视频还是图文"""
        try:
            print(f"检测抖音链接类型：{url}")
            
            # 访问链接获取HTML内容
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Referer': 'https://www.douyin.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                print(f"访问抖音链接失败，状态码：{response.status_code}，默认返回视频类型")
                return 'video'
            
            html_content = response.text
            
            # 方法1：从JSON数据中提取类型信息
            match = re.search(r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.*?})</script>', html_content, re.DOTALL)
            if not match:
                match = re.search(r'window\._SSR_HYDRATED_DATA\s*=\s*({.*?});', html_content, re.DOTALL)
            
            if match:
                try:
                    json_data = json.loads(match.group(1))
                    
                    # 检查是否是图文类型
                    if 'app' in json_data and 'videoInfo' in json_data['app']:
                        video_info = json_data['app']['videoInfo']
                        
                        # 检查awemeType字段：2表示图文，0或4表示视频
                        if 'awemeType' in video_info:
                            aweme_type = video_info['awemeType']
                            print(f"  检测到awemeType: {aweme_type}")
                            if aweme_type == 2:
                                print("  ✓ 检测到抖音图文")
                                return 'douyin_image'
                            else:
                                print(f"  ✓ 检测到抖音视频 (type={aweme_type})")
                                return 'video'
                        
                        # 检查是否有图片列表
                        if 'images' in video_info and video_info['images']:
                            print(f"  ✓ 检测到图片列表，共 {len(video_info['images'])} 张")
                            return 'douyin_image'
                        
                        # 检查是否有视频信息
                        if 'video' in video_info and video_info['video']:
                            print("  ✓ 检测到视频信息")
                            return 'video'
                
                except json.JSONDecodeError as e:
                    print(f"  JSON解析失败: {e}")
            
            # 方法2：检查HTML中的特征
            # 检查是否有图片画廊的特征
            if 'image-gallery' in html_content or 'imageList' in html_content:
                print("  ✓ 检测到图片画廊特征")
                return 'douyin_image'
            
            # 检查是否有视频播放器的特征
            video_indicators = ['video-player', 'player-container', 'xigua-video', 'videoDuration']
            for indicator in video_indicators:
                if indicator in html_content:
                    print(f"  ✓ 检测到视频特征: {indicator}")
                    return 'video'
            
            # 方法3：检查URL特征
            # 某些图文链接有特定特征
            if '/note/' in url or 'modal_id=' in url:
                # 进一步检查内容
                if 'slide' in html_content.lower() or 'gallery' in html_content.lower():
                    print("  ✓ URL和内容特征表明是图文")
                    return 'douyin_image'
            
            # 默认返回视频类型（保守策略）
            print("  未检测到明确类型，默认返回视频")
            return 'video'
            
        except Exception as e:
            print(f"检测抖音链接类型出错：{e}")
            return 'video'  # 出错时默认返回视频类型
    
    def _analyze_video(self, url):
        """分析视频链接"""
        # 这里可以集成现有的视频分析逻辑
        return {
            'type': 'video',
            'url': url,
            'message': '视频链接，需要使用视频分析逻辑'
        }
    
    def _extract_image_count(self, html_content):
        """从 HTML 内容中提取图片总数"""
        # 方法 1：从 meta 标签的 og:image 数量判断
        meta_count = len(re.findall(r'<meta[^>]*name="og:image"[^>]*>', html_content))
        if meta_count > 0:
            return meta_count
        
        # 方法 2：从 JSON 数据中提取
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                if 'note' in json_data and 'noteDetailMap' in json_data['note']:
                    for note_id, note_data in json_data['note']['noteDetailMap'].items():
                        if 'note' in note_data and 'imageList' in note_data['note']:
                            return len(note_data['note']['imageList'])
            except:
                pass
        
        # 方法 3：从页面中的图片计数器提取（如 "1/6" 格式）
        counter_match = re.search(r'(\d+)\s*/\s*(\d+)', html_content)
        if counter_match:
            return int(counter_match.group(2))
        
        return None
    
    def _detect_xiaohongshu_type(self, html_content):
        """检测小红书链接是视频还是图文"""
        # 方法1：检查是否有视频相关的meta标签
        video_patterns = [
            r'<meta[^>]*property="og:video"[^>]*>',
            r'<meta[^>]*name="og:video"[^>]*>',
            r'<meta[^>]*property="og:video:url"[^>]*>',
            r'"type":"video"',
            r'"type":\s*"video"',
            r'"video"',
            r'videoUrl',
            r'video_id',
            r'videoDuration',
            r'consumer\":{[^}]*"video"',
            r'consumer":\s*{"video"'
        ]
        for pattern in video_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                print(f"  检测到视频特征: {pattern[:50]}...")
                return 'video'
        
        # 方法2：从JSON数据中提取类型信息
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', html_content, re.DOTALL)
        if match:
            try:
                json_data = json.loads(match.group(1))
                if 'note' in json_data and 'noteDetailMap' in json_data['note']:
                    for note_id, note_data in json_data['note']['noteDetailMap'].items():
                        if 'note' in note_data:
                            note = note_data['note']
                            # 检查类型字段
                            if 'type' in note:
                                note_type = note['type']
                                print(f"  检测到笔记类型: {note_type}")
                                if note_type == 'video':
                                    return 'video'
                                elif note_type == 'normal':
                                    return 'xiaohongshu'  # 图文
                            # 检查是否有视频链接
                            if 'video' in note or 'videoUrl' in note or 'video_url' in note:
                                print(f"  检测到视频URL字段")
                                return 'video'
                            # 检查是否有视频时长
                            if 'videoDuration' in note or 'video_duration' in note:
                                print(f"  检测到视频时长字段")
                                return 'video'
                            # 检查图片列表
                            if 'imageList' in note and len(note['imageList']) > 0:
                                print(f"  检测到图片列表，共 {len(note['imageList'])} 张")
                                return 'xiaohongshu'  # 有图片，认为是图文
            except Exception as e:
                print(f"  JSON解析失败: {e}")
        
        # 方法3：检查URL特征（某些视频链接有特定特征）
        if 'video' in html_content[:5000].lower():
            # 检查是否包含视频播放器的特征
            player_patterns = [
                r'video-player',
                r'videoPlayer',
                r'xigua-video',
                r'player-container'
            ]
            for pattern in player_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    print(f"  检测到视频播放器特征: {pattern}")
                    return 'video'
        
        # 默认返回图文类型（保守策略）
        print(f"  未检测到明确类型，默认返回图文")
        return 'xiaohongshu'
    
    def _analyze_xiaohongshu(self, url):
        """分析小红书链接"""
        try:
            # 访问链接
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return {
                    'type': 'xiaohongshu',
                    'url': url,
                    'error': f'访问失败，状态码：{response.status_code}'
                }
            
            # 【关键】检测是视频还是图文
            html_content = response.text
            content_type = self._detect_xiaohongshu_type(html_content)
            print(f"小红书内容类型检测结果：{content_type}")
            
            # 如果是视频，返回视频类型
            if content_type == 'video':
                print(f"✓ 检测到小红书视频")
                return {
                    'type': 'video',
                    'url': url,
                    'message': '小红书视频，需要使用视频分析逻辑'
                }
            
            # 备用检测：如果HTML内容很少或包含特定视频标记，可能是视频
            if len(html_content) < 5000 or 'video' in html_content[:3000].lower():
                # 检查是否有视频相关的关键特征
                video_indicators = ['video-player', 'player-container', 'xigua-video', 'videoDuration']
                for indicator in video_indicators:
                    if indicator in html_content:
                        print(f"✓ 备用检测发现视频特征: {indicator}")
                        return {
                            'type': 'video',
                            'url': url,
                            'message': '小红书视频（备用检测），需要使用视频分析逻辑'
                        }
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', response.text)
            title = title_match.group(1) if title_match else '未知标题'
            
            # 检测图片总数
            expected_image_count = self._extract_image_count(response.text)
            if expected_image_count:
                print(f"检测到笔记应有 {expected_image_count} 张图片")
            
            # 提取图片链接
            image_links = []
            
            # 方法 1：从 meta 标签的 og:image 属性提取（小红书图片通常在这里）
            # 尝试 name 属性
            meta_tags = soup.find_all('meta', attrs={'name': 'og:image'})
            for meta in meta_tags:
                content = meta.get('content')
                if content and 'xhscdn.com' in content:
                    image_links.append(content)
            
            # 尝试 property 属性（备用）
            if not image_links:
                meta_tags = soup.find_all('meta', property='og:image')
                for meta in meta_tags:
                    content = meta.get('content')
                    if content and 'xhscdn.com' in content:
                        image_links.append(content)
            
            # 方法 2：从 script 标签提取 JSON 数据
            if not image_links:
                script_tags = soup.find_all('script')
                for script in script_tags:
                    script_text = script.get_text()
                    if '__INITIAL_STATE__' in script_text:
                        # 提取 JSON 部分
                        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_text, re.DOTALL)
                        if match:
                            try:
                                json_data = json.loads(match.group(1))
                                # 提取图片链接
                                if 'note' in json_data and 'noteDetailMap' in json_data['note']:
                                    for note_id, note_data in json_data['note']['noteDetailMap'].items():
                                        if 'note' in note_data and 'imageList' in note_data['note']:
                                            for img in note_data['note']['imageList']:
                                                if 'urlDefault' in img:
                                                    image_links.append(img['urlDefault'])
                            except json.JSONDecodeError:
                                pass
            
            # 方法 3：如果上述方法都失败，直接从 HTML 提取图片
            if not image_links:
                img_tags = soup.find_all('img')
                for img in img_tags:
                    src = img.get('src')
                    if src and ('http' in src) and not ('gif' in src):
                        image_links.append(src)
            
            # 去重
            image_links = list(dict.fromkeys(image_links))
            
            print(f"共提取到 {len(image_links)} 张图片")
            
            # 验证图片数量
            if expected_image_count and len(image_links) < expected_image_count:
                print(f"警告：只提取到 {len(image_links)} 张图片，但应有 {expected_image_count} 张")
                print("尝试从其他来源补充图片链接...")
                
                # 尝试从页面中的其他位置提取图片
                # 查找所有包含 xhscdn.com 的链接
                all_links = re.findall(r'https?://[^\s"\'<>]+xhscdn\.com[^\s"\'<>]*', response.text)
                for link in all_links:
                    if link not in image_links and '!nd_' in link:
                        image_links.append(link)
                
                # 再次去重
                image_links = list(dict.fromkeys(image_links))
                print(f"补充后共 {len(image_links)} 张图片")
            
            # 提取文本内容
            text_content = []
            
            # 从 script 标签提取文本
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_text = script.get_text()
                if '__INITIAL_STATE__' in script_text:
                    match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_text, re.DOTALL)
                    if match:
                        try:
                            json_data = json.loads(match.group(1))
                            if 'note' in json_data and 'noteDetailMap' in json_data['note']:
                                for note_id, note_data in json_data['note']['noteDetailMap'].items():
                                    if 'note' in note_data and 'desc' in note_data['note']:
                                        text_content.append(note_data['note']['desc'])
                        except json.JSONDecodeError:
                            pass
            
            # 直接从 HTML 提取文本
            if not text_content:
                divs = soup.find_all('div')
                for div in divs:
                    text = div.get_text(strip=True)
                    if text and len(text) > 50:
                        text_content.append(text)
            
            # 分析图片内容（分析所有提取到的图片）
            import time
            image_analysis = []
            for i, img_url in enumerate(image_links):
                print(f"分析图片 {i+1}/{len(image_links)}: {img_url}")
                img_data = self.download_image(img_url)
                if img_data:
                    ocr_result = self.ocr_image(img_data)
                    if ocr_result:
                        img_text = self.extract_text_from_ocr(ocr_result)
                        image_analysis.append({
                            'url': img_url,
                            'text': img_text
                        })
                
                # 添加延时，避免触发百度 OCR 的 QPS 限制
                if i < len(image_links) - 1:  # 最后一张图片不需要等待
                    time.sleep(1.0)  # 等待 1 秒
            
            # 生成总结
            summary = self._generate_summary(title, text_content, image_analysis)
            
            return {
                'type': 'xiaohongshu',
                'url': url,
                'title': title,
                'text_content': '\n'.join(text_content),
                'image_links': image_links,
                'image_analysis': image_analysis,
                'expected_image_count': expected_image_count,
                'summary': summary
            }
            
        except Exception as e:
            print(f"分析小红书链接出错：{e}")
            import traceback
            traceback.print_exc()
            return {
                'type': 'xiaohongshu',
                'url': url,
                'error': str(e)
            }
    
    def _analyze_douyin_image(self, url):
        """分析抖音图文链接 - 仿照小红书实现"""
        try:
            print(f"开始分析抖音图文：{url}")
            
            # 访问链接
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
                'Referer': 'https://www.douyin.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                return {
                    'type': 'douyin_image',
                    'url': url,
                    'error': f'访问失败，状态码：{response.status_code}'
                }
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取标题
            title_match = re.search(r'<title>(.*?)</title>', html_content)
            title = title_match.group(1) if title_match else '抖音图文'
            
            # 提取图片链接
            image_links = []
            
            # 方法1：从JSON数据中提取（抖音图文的主要方式）
            match = re.search(r'<script[^>]*>window\._SSR_HYDRATED_DATA\s*=\s*({.*?})</script>', html_content, re.DOTALL)
            if not match:
                match = re.search(r'window\._SSR_HYDRATED_DATA\s*=\s*({.*?});', html_content, re.DOTALL)
            
            if match:
                try:
                    json_data = json.loads(match.group(1))
                    
                    if 'app' in json_data and 'videoInfo' in json_data['app']:
                        video_info = json_data['app']['videoInfo']
                        
                        # 提取图片列表
                        if 'images' in video_info and video_info['images']:
                            for img in video_info['images']:
                                # 抖音图片可能有多个URL，优先使用高清晰度的
                                if 'urlList' in img and img['urlList']:
                                    # 使用第一张（通常是最高清的）
                                    image_links.append(img['urlList'][0])
                                elif 'url' in img:
                                    image_links.append(img['url'])
                                elif 'coverUrl' in img:
                                    image_links.append(img['coverUrl'])
                        
                        # 提取文本内容
                        text_content = []
                        if 'desc' in video_info:
                            text_content.append(video_info['desc'])
                        
                        # 提取作者信息
                        author_name = ''
                        if 'authorInfo' in video_info and 'nickname' in video_info['authorInfo']:
                            author_name = video_info['authorInfo']['nickname']
                        
                        print(f"从JSON提取到 {len(image_links)} 张图片")
                
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
            
            # 方法2：从meta标签提取（备用）
            if not image_links:
                meta_tags = soup.find_all('meta', property='og:image')
                for meta in meta_tags:
                    content = meta.get('content')
                    if content:
                        image_links.append(content)
            
            # 方法3：从HTML中查找所有图片链接（备用）
            if not image_links:
                # 查找所有包含douyincdn.com或p3-pc-sign.douyinpic.com的图片链接
                all_links = re.findall(r'https?://[^\s"\'<>]+(?:douyincdn\.com|douyinpic\.com)[^\s"\'<>]*', html_content)
                for link in all_links:
                    if link not in image_links:
                        image_links.append(link)
            
            # 去重
            image_links = list(dict.fromkeys(image_links))
            print(f"共提取到 {len(image_links)} 张图片")
            
            # 提取文本内容（如果之前没有提取到）
            if 'text_content' not in locals():
                text_content = []
                
                # 从meta标签提取描述
                desc_meta = soup.find('meta', attrs={'name': 'description'})
                if desc_meta:
                    text_content.append(desc_meta.get('content', ''))
                
                # 从HTML中提取文本
                if not text_content:
                    divs = soup.find_all('div')
                    for div in divs:
                        text = div.get_text(strip=True)
                        if text and len(text) > 20:
                            text_content.append(text)
            
            # 分析图片内容（使用OCR）
            import time
            image_analysis = []
            for i, img_url in enumerate(image_links):
                print(f"分析图片 {i+1}/{len(image_links)}: {img_url[:60]}...")
                img_data = self.download_image(img_url)
                if img_data:
                    ocr_result = self.ocr_image(img_data)
                    if ocr_result:
                        img_text = self.extract_text_from_ocr(ocr_result)
                        image_analysis.append({
                            'url': img_url,
                            'text': img_text
                        })
                
                # 添加延时，避免触发百度 OCR 的 QPS 限制
                if i < len(image_links) - 1:
                    time.sleep(1.0)
            
            # 生成总结
            summary = self._generate_summary(title, text_content, image_analysis)
            
            return {
                'type': 'douyin_image',
                'url': url,
                'title': title,
                'text_content': '\n'.join(text_content),
                'image_links': image_links,
                'image_analysis': image_analysis,
                'author': author_name if 'author_name' in locals() else '',
                'summary': summary
            }
            
        except Exception as e:
            print(f"分析抖音图文出错：{e}")
            import traceback
            traceback.print_exc()
            return {
                'type': 'douyin_image',
                'url': url,
                'error': str(e)
            }
    
    def _analyze_general(self, url):
        """分析通用链接"""
        try:
            # 访问链接
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                return {
                    'type': 'general',
                    'url': url,
                    'error': f'访问失败，状态码：{response.status_code}'
                }
            
            # 提取标题
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title').text if soup.find('title') else '未知标题'
            
            # 提取图片
            img_tags = soup.find_all('img')
            image_links = []
            for img in img_tags:
                src = img.get('src')
                if src and ('http' in src) and not ('gif' in src):
                    image_links.append(src)
            
            # 提取文本
            text_content = soup.get_text(separator='\n', strip=True)
            
            return {
                'type': 'general',
                'url': url,
                'title': title,
                'text_content': text_content[:1000],  # 限制文本长度
                'image_links': image_links[:5]  # 只返回前 5 张图片
            }
            
        except Exception as e:
            print(f"分析通用链接出错：{e}")
            return {
                'type': 'general',
                'url': url,
                'error': str(e)
            }
    
    def _clean_text(self, text):
        """清理文本，删除版权信息等无关内容"""
        # 删除版权信息和无关内容
        copyright_patterns = [
            r'登录我沪ICP 备.*?号',
            r'营业执照.*?号',
            r'沪公网安备.*?号',
            r'增值电信业务经营许可证.*?号',
            r'医疗器械网络交易服务第三方平台备案.*?号',
            r'互联网药品信息服务资格证书.*?号',
            r'违法不良信息举报电话.*?',
            r'上海市互联网举报中心',
            r'网上有害信息举报专区',
            r'自营经营者信息',
            r'网络文化经营许可证.*?号',
            r'个性化推荐算法.*?号',
            r'© 2014-2024 行吟信息科技.*?有限公司',
            r'地址：上海市黄浦区马当路 388 号 C 座',
            r'电话：9501-3888',
            r'创作中心业务合作发现发布通知.*?',
            r'更多沪ICP 备.*?号',
            r'Y\.g\.关注.*?加载中',
            r'#面试手撕#算法岗手撕#大模型算法 2025-10-28',
            r'#面试手撕#算法岗手撕#大模型算法',
            r'\[doge\]',
            r'沪ICP 备 13030189 号',
            r'\|\|\|\|\|\|\|\|',
            r'加载中'
        ]
        
        cleaned_text = text
        for pattern in copyright_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # 删除多余的空格和换行
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def _generate_summary(self, title, text_content, image_analysis):
        """生成总结"""
        # 清理标题
        clean_title = re.sub(r' - 小红书$', '', title)
        summary = f"# {clean_title}\n\n"
        
        # 提取并清理文本内容
        cleaned_texts = []
        if text_content:
            for text in text_content:
                cleaned = self._clean_text(text)
                if cleaned and len(cleaned) > 10:
                    cleaned_texts.append(cleaned)
        
        # 添加文本内容摘要
        if cleaned_texts:
            summary += "## 文本内容\n"
            # 合并所有文本内容
            combined_text = ' '.join(cleaned_texts)
            # 提取核心内容
            core_content = combined_text[:500] + ('...' if len(combined_text) > 500 else '')
            summary += core_content + '\n\n'
        
        # 整合所有图片内容
        all_image_texts = []
        if image_analysis:
            for img_analysis in image_analysis:
                if img_analysis['text']:
                    cleaned_img_text = self._clean_text(img_analysis['text'])
                    if cleaned_img_text:
                        all_image_texts.append(cleaned_img_text)
        
        # 添加整合后的图片内容
        if all_image_texts:
            summary += "## 图片内容\n"
            for i, img_text in enumerate(all_image_texts):
                summary += f"### 图片 {i+1} 内容\n"
                summary += img_text + '\n\n'
        
        return summary
    
    def _get_platform(self, url):
        """从 URL 中提取平台信息"""
        if 'xiaohongshu.com' in url:
            return '小红书'
        elif 'douyin.com' in url or 'tiktok.com' in url:
            return '抖音'
        elif 'bilibili.com' in url:
            return 'B 站'
        elif 'youtube.com' in url:
            return 'YouTube'
        else:
            return '网页'
    
    def _get_output_filename(self, platform, title, link_type=None):
        """生成统一格式的输出文件名，与原有格式保持一致"""
        import time
        import re
        import os
        
        # 获取当前日期（月 - 日格式）
        date_str = time.strftime('%m-%d', time.localtime())
        
        # 清理标题，用于文件名
        clean_title = re.sub(r'[^\w\u4e00-\u9fa5]', '_', title)
        clean_title = clean_title[:30].strip('_')
        if not clean_title:
            clean_title = 'untitled'
        
        # 生成前缀数字（基于现有文件数量）
        output_dir = os.path.join(os.path.dirname(__file__), 'OUTPUT')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 计算现有文件数量，生成前缀
        existing_files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
        prefix_num = len(existing_files) + 1
        prefix = f"{prefix_num:03d}"
        
        # 确定文件类型后缀
        if link_type == 'douyin_image':
            suffix = '_抖音图文分析.md'
        elif platform == '抖音' or platform == 'B 站' or platform == 'YouTube':
            suffix = '_视频分析.md'
        else:
            suffix = '_内容分析.md'
        
        # 生成文件名
        filename = f"{prefix}-{date_str}-{clean_title}{suffix}"
        return filename
    
    def generate_markdown(self, analysis_result, output_file=None):
        """生成 Markdown 文件，包含原始内容和 AI 分析摘要"""
        try:
            import os
            import time
            
            # 获取分析结果的基本信息
            url = analysis_result.get('url', '')
            title = analysis_result.get('title', '未命名')
            summary = analysis_result.get('summary', '')
            link_type = analysis_result.get('type', 'general')
            expected_image_count = analysis_result.get('expected_image_count', None)
            actual_image_count = len(analysis_result.get('image_links', []))
            
            # 提取平台信息
            platform = self._get_platform(url)
            
            # 生成当前时间
            datetime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            
            # 创建 OUTPUT 文件夹（如果不存在）
            output_dir = os.path.join(os.path.dirname(__file__), 'OUTPUT')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成输出文件名
            if not output_file:
                filename = self._get_output_filename(platform, title, link_type)
                output_file = os.path.join(output_dir, filename)
            else:
                # 如果指定了输出文件，确保它在 OUTPUT 文件夹中
                if not output_file.startswith(output_dir):
                    output_file = os.path.join(output_dir, os.path.basename(output_file))
            
            # 生成完整的 Markdown 内容
            full_content = ""
            
            # 添加原始内容（直接转化成的文字）
            full_content += summary
            
            # 添加图片数量信息
            if expected_image_count:
                full_content += f"\n## 图片统计\n"
                full_content += f"- 应有图片数：{expected_image_count}\n"
                full_content += f"- 实际提取：{actual_image_count}\n"
                if actual_image_count < expected_image_count:
                    full_content += f"- 状态：部分图片可能未成功提取\n"
                else:
                    full_content += f"- 状态：全部提取成功\n"
                full_content += "\n"
            
            # 添加 AI 分析摘要部分
            full_content += "\n## AI 分析摘要\n"
            full_content += f"# {platform}内容分析\n"
            full_content += "## 内容信息\n"
            full_content += f"- 分析时间：{datetime_str}\n"
            full_content += f"- 原始链接：{url}\n"
            full_content += f"- 平台：{platform}\n"
            full_content += f"- 类型：{'视频' if link_type == 'video' else '图文'}\n"
            
            # 调用 video_gui.py 中的 summarize_with_volcengine 方法进行 AI 分析
            try:
                # 导入 video_gui 模块
                from video_gui import App, CONFIG, DEFAULT_CONFIG, VOLCENGINE_API_KEY, VOLCENGINE_API_URL
                
                # 创建临时的 App 实例来调用 summarize_with_volcengine 方法
                # 由于 App 需要 root 窗口，我们创建一个临时的
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()  # 隐藏窗口
                app = App(root)
                
                # 调用 AI 分析方法
                ai_analysis = app.summarize_with_volcengine(summary, "")
                
                if ai_analysis:
                    full_content += ai_analysis
                else:
                    full_content += "\n## 1. 内容概览\nAI 分析暂不可用\n\n## 2. 核心要点\n- 暂无\n\n## 3. 详细分析\n暂无\n\n## 4. 总结\n暂无\n"
                
                root.destroy()
            except Exception as e:
                print(f"调用 AI 分析接口失败：{e}")
                full_content += "\n## 1. 内容概览\nAI 分析调用失败\n\n## 2. 核心要点\n- 暂无\n\n## 3. 详细分析\n暂无\n\n## 4. 总结\n暂无\n"
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            print(f"Markdown 文件生成成功：{output_file}")
            return True
        except Exception as e:
            print(f"生成 Markdown 文件出错：{e}")
            import traceback
            traceback.print_exc()
            return False

# 测试函数
if __name__ == "__main__":
    analyzer = LinkAnalyzer()
    
    # 测试小红书链接
    test_url = 'https://www.xiaohongshu.com/explore/6900d1c70000000007035e79?app_platform=android&ignoreEngage=true&app_version=9.19.4&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M=&author_share=1&xhsshare=&shareRedId=ODZGQzVKNz02NzUyOTgwNjY0OTc8RjdP&apptime=1771134517&share_id=cf150dbd16f94855950aa3d742a6f7fd&share_channel=wechat'
    
    result = analyzer.analyze_link(test_url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 生成 Markdown 文件（使用统一命名）
    analyzer.generate_markdown(result)
