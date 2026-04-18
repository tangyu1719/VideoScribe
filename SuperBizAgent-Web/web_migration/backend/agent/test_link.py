# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')

try:
    import link_analyzer
    print("✓ link_analyzer 导入成功")
    
    # 测试视频检测
    analyzer = link_analyzer.LinkAnalyzer()
    test_url = 'https://www.xiaohongshu.com/explore/69b292500000000028009849?xsec_token=ABooHNtmLa1lywHSX_GfvOvOK5_vdc3sq0jATYVEa0qMo=&xsec_source=pc_collect'
    print(f"\n开始测试链接：{test_url}")
    result = analyzer.analyze_link(test_url)
    print(f"\n分析结果类型：{result.get('type')}")
    print(f"标题：{result.get('title')}")
    if result.get('type') == 'video':
        print("✓ 成功识别为视频链接！")
    elif result.get('type') == 'xiaohongshu':
        print("⚠ 识别为图文链接")
    else:
        print(f"结果：{result}")
        
except Exception as e:
    print(f"✗ 错误：{e}")
    import traceback
    traceback.print_exc()
