from aip import AipOcr
import requests

# 百度OCR API配置
APP_ID = '122094788'
API_KEY = 'KZOpVw7PGLRiBdsqRnuLFVY7'
SECRET_KEY = 'L1pdbtb4IZZv67ofXnsxDNAhELGN2UXs'

# 初始化AipOcr
client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 测试图片链接
test_image_url = 'http://sns-webpic-qc.xhscdn.com/202603112231/b9490062701dc805c320ea12b46daccd/spectrum/1040g34o31o26t0lkl0805nipqo1g8h6ao4vm7ng!nd_dft_wlteh_jpg_3'

def download_image(url):
    """下载图片并返回二进制数据"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.content
        else:
            print(f"下载图片失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"下载图片出错: {e}")
        return None

def test_baidu_ocr():
    """测试百度OCR API"""
    print("测试百度OCR API...")
    print(f"AppID: {APP_ID}")
    print(f"API Key: {API_KEY}")
    print(f"Secret Key: {SECRET_KEY}")
    
    # 下载图片
    image_data = download_image(test_image_url)
    if not image_data:
        print("图片下载失败，测试终止")
        return
    
    print(f"图片大小: {len(image_data)} bytes")
    
    # 测试OCR识别
    try:
        # 调用通用文字识别（高精度版）
        print("开始OCR识别...")
        result = client.basicAccurate(image_data)
        
        if result:
            print("OCR识别成功！")
            if 'words_result' in result:
                print(f"识别到 {len(result['words_result'])} 个文字区域")
                for i, item in enumerate(result['words_result']):
                    print(f"{i+1}. {item['words']}")
            else:
                print("OCR结果中没有文字")
        else:
            print("OCR识别失败，返回空结果")
            
    except Exception as e:
        print(f"OCR识别出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_baidu_ocr()
