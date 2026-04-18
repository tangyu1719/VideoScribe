from aip import AipOcr
import requests
import re
import json
from bs4 import BeautifulSoup
import os

class LinkAnalyzerDebug:
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
                print(f"下载图片失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"下载图片出错: {e}")
            return None
    
    def ocr_image(self, image_data):
        """使用百度OCR识别图片文字"""
        try:
            # 调用通用文字识别（高精度版）
            result = self.client.basicAccurate(image_data)
            return result
        except Exception as e:
            print(f"OCR识别出错: {e}")
            return None
    
    def extract_text_from_ocr(self, result):
        """从OCR结果中提取文本"""
        if not result or 'words_result' not in result:
            return ""
        
        text = ""
        for item in result['words_result']:
            text += item['words'] + '\n'
        
        return text
    
    def test_image_ocr(self, img_url, img_index):
        """测试单张图片的OCR"""
        print(f"\n{'='*60}")
        print(f"测试图片 {img_index}: {img_url}")
        print(f"{'='*60}")
        
        img_data = self.download_image(img_url)
        if not img_data:
            print("下载失败")
            return None
        
        print(f"图片大小: {len(img_data)} bytes")
        
        ocr_result = self.ocr_image(img_data)
        if not ocr_result:
            print("OCR失败")
            return None
        
        print(f"OCR结果: {json.dumps(ocr_result, ensure_ascii=False, indent=2)}")
        
        text = self.extract_text_from_ocr(ocr_result)
        print(f"\n提取文本长度: {len(text)}")
        print(f"提取文本:\n{text}")
        
        return text

# 测试所有6张图片
analyzer = LinkAnalyzerDebug()

# 6张图片URL
image_urls = [
    'http://sns-webpic-qc.xhscdn.com/202602152316/1a7df8f05255c9744b8a28ce18e7611c/1040g2sg31o6f1o5kkqkg5pdgt9smcerrrsoknug!nd_dft_wlteh_jpg_3',
    'http://sns-webpic-qc.xhscdn.com/202602152316/e6775de302a879e73f7dc2e8c7bb6cdf/1040g2sg31o6fr8s4ku005pdgt9smcerr47ntroo!nd_dft_wlteh_jpg_3',
    'http://sns-webpic-qc.xhscdn.com/202602152316/6f8744d8a66f935e3e0c5015a651b656/1040g2sg31o6fr9cbku005pdgt9smcerrim4trl8!nd_dft_wlteh_jpg_3',
    'http://sns-webpic-qc.xhscdn.com/202602152316/c2d91c5fdf0b5843c058da95b62c96f8/1040g2sg31o6fr99o4ul05pdgt9smcerr5g5hs88!nd_dft_wlteh_jpg_3',
    'http://sns-webpic-qc.xhscdn.com/202602152316/1356aed48faf60233c818d4695cbd1b1/1040g2sg31o6fr92o4u005pdgt9smcerrfqrld7o!nd_dft_wlteh_jpg_3',
    'http://sns-webpic-qc.xhscdn.com/202602152316/77bb6ceb0c632af1bc24079a446d6e7a/1040g2sg31o6fr8v950005pdgt9smcerrs0v6jf8!nd_dft_wgth_jpg_3'
]

for i, url in enumerate(image_urls, 1):
    analyzer.test_image_ocr(url, i)
