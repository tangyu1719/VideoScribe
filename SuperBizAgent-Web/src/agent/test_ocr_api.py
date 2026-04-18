from aip import AipOcr
import requests
import base64
import json

# 百度OCR API配置
APP_ID = '122094788'
API_KEY = 'KZOpVw7PGLRiBdsqRnuLFVY7'
SECRET_KEY = 'L1pdbtb4IZZv67ofXnsxDNAhELGN2UXs'

# 初始化AipOcr
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 小红书测试链接
TEST_URL = 'https://www.xiaohongshu.com/explore/6900d1c70000000007035e79?app_platform=android&ignoreEngage=true&app_version=9.19.4&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CByoAevCF6QXsWDyTWZ1v8FmKxp4mmicBjb5euatwe84M=&author_share=1&xhsshare=&shareRedId=ODZGQzVKNz02NzUyOTgwNjY0OTc8RjdP&apptime=1771134517&share_id=cf150dbd16f94855950aa3d742a6f7fd&share_channel=wechat'

# 从之前提取的图片链接
IMAGE_URLS = [
    'http://sns-webpic-qc.xhscdn.com/202602151515/b68355a7de74e9d9d3ffa2b9893263f2/1040g2sg31o6f1o5kkqkg5pdgt9smcerrrsoknug!nd_dft_wlteh_jpg_3',
    'http://sns-webpic-qc.xhscdn.com/202602151515/df63ab0aba8a9380e50b275e1b64f7e6/1040g2sg31o6fr8s4ku005pdgt9smcerr47ntroo!nd_dft_wlteh_jpg_3'
]

def download_image(url):
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

def ocr_image(image_data):
    """使用百度OCR识别图片文字"""
    try:
        # 调用通用文字识别（高精度版）
        result = client.basicAccurate(image_data)
        return result
    except Exception as e:
        print(f"OCR识别出错: {e}")
        return None

def extract_text_from_ocr(result):
    """从OCR结果中提取文本"""
    if not result or 'words_result' not in result:
        return ""
    
    text = ""
    for item in result['words_result']:
        text += item['words'] + '\n'
    
    return text

def test_ocr_api():
    """测试OCR API功能"""
    print("测试百度OCR API...")
    print(f"AppID: {APP_ID}")
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY}")
    
    # 测试图片OCR
    for i, image_url in enumerate(IMAGE_URLS):
        print(f"\n测试图片 {i+1}: {image_url}")
        
        # 下载图片
        image_data = download_image(image_url)
        if not image_data:
            print(f"跳过图片 {i+1}，下载失败")
            continue
        
        print(f"图片大小: {len(image_data)} bytes")
        
        # 进行OCR识别
        ocr_result = ocr_image(image_data)
        if not ocr_result:
            print(f"跳过图片 {i+1}，OCR识别失败")
            continue
        
        print(f"OCR结果: {json.dumps(ocr_result, ensure_ascii=False, indent=2)}")
        
        # 提取文本
        text = extract_text_from_ocr(ocr_result)
        print(f"提取的文本: {text}")
    
    print("\nOCR API测试完成！")

if __name__ == "__main__":
    test_ocr_api()
