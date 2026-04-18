import requests
from aip import AipOcr

# 百度OCR API配置
APP_ID = '122094788'
API_KEY = 'KZOpVw7PGLRiBdsqRnuLFVY7'
SECRET_KEY = 'L1pdbtb4IZZv67ofXnsxDNAhELGN2UXs'

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

# 第5张图片URL
img_url = 'http://sns-webpic-qc.xhscdn.com/202602152316/1356aed48faf60233c818d4695cbd1b1/1040g2sg31o6fr92o4u005pdgt9smcerrfqrld7o!nd_dft_wlteh_jpg_3'

print(f"下载图片: {img_url}")
response = requests.get(img_url, timeout=15)
print(f"下载状态: {response.status_code}")

if response.status_code == 200:
    img_data = response.content
    print(f"图片大小: {len(img_data)} bytes")
    
    # 保存图片到本地，方便查看
    with open('image5.jpg', 'wb') as f:
        f.write(img_data)
    print("图片已保存到 image5.jpg")
    
    # 尝试OCR识别
    print("\n尝试OCR识别...")
    result = client.basicAccurate(img_data)
    print(f"OCR结果: {result}")
    
    if 'words_result' in result:
        print(f"\n识别到 {len(result['words_result'])} 行文字:")
        for i, item in enumerate(result['words_result']):
            print(f"  {i+1}: {item['words']}")
    else:
        print("\n未识别到文字")
        if 'error_msg' in result:
            print(f"错误信息: {result['error_msg']}")
        if 'error_code' in result:
            print(f"错误码: {result['error_code']}")
    
    # 尝试通用文字识别（标准版）
    print("\n尝试通用文字识别（标准版）...")
    result2 = client.basicGeneral(img_data)
    print(f"标准版OCR结果: {result2}")
    
    if 'words_result' in result2:
        print(f"\n标准版识别到 {len(result2['words_result'])} 行文字:")
        for i, item in enumerate(result2['words_result']):
            print(f"  {i+1}: {item['words']}")
    else:
        print("\n标准版未识别到文字")
        if 'error_msg' in result2:
            print(f"错误信息: {result2['error_msg']}")
