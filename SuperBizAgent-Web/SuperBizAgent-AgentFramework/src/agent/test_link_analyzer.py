from link_analyzer import LinkAnalyzer
import json

analyzer = LinkAnalyzer()

# 测试第5张图片
test_url = 'http://sns-webpic-qc.xhscdn.com/202602152316/1356aed48faf60233c818d4695cbd1b1/1040g2sg31o6fr92o4u005pdgt9smcerrfqrld7o!nd_dft_wlteh_jpg_3'

print("下载图片...")
img_data = analyzer.download_image(test_url)
if img_data:
    print(f"图片大小: {len(img_data)} bytes")
    
    print("\n进行OCR识别...")
    ocr_result = analyzer.ocr_image(img_data)
    print(f"OCR结果类型: {type(ocr_result)}")
    print(f"OCR结果: {json.dumps(ocr_result, ensure_ascii=False, indent=2)}")
    
    print("\n提取文本...")
    text = analyzer.extract_text_from_ocr(ocr_result)
    print(f"提取的文本: '{text}'")
    print(f"文本长度: {len(text)}")
else:
    print("下载图片失败")
