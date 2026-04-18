import requests

# 测试图片链接
test_image_url = 'http://sns-webpic-qc.xhscdn.com/202603112231/b9490062701dc805c320ea12b46daccd/spectrum/1040g34o31o26t0lkl0805nipqo1g8h6ao4vm7ng!nd_dft_wlteh_jpg_3'

def test_image_download():
    """测试图片下载"""
    print(f"测试下载图片: {test_image_url}")
    
    try:
        # 设置headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Referer': 'https://www.xiaohongshu.com/',
        }
        
        # 下载图片
        response = requests.get(test_image_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ 下载成功！图片大小: {len(response.content)} bytes")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            return True
        else:
            print(f"❌ 下载失败，状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            return False
    except Exception as e:
        print(f"❌ 下载出错: {e}")
        return False

if __name__ == "__main__":
    test_image_download()
