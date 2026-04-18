#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号文章批量处理测试
测试多线程环境下文章提取的稳定性
"""

import os
import sys
import time
import concurrent.futures
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wechat_article_processor import WeChatArticleProcessor

# 测试链接列表
test_urls = [
    'https://mp.weixin.qq.com/s/sePut6awebQRWDxfJYqO9g',  # 把 WMS 系统彻底讲清楚
    'https://mp.weixin.qq.com/s/4EjAG1LblkyeZuLeznSuHw|',  # 无效链接（带|）
    'https://mp.weixin.qq.com/s/ojdQuW_13Vtr1c0MnNIQDQ',   # 一文带你秒懂 SaaS
    'https://mp.weixin.qq.com/s/7uMyf62I3FQi3UpMoEYvmg',   # 月底盘点
]

def process_single_article(url, index):
    """处理单篇文章"""
    print(f"\n{'='*60}")
    print(f"【任务 {index+1}】处理链接: {url}")
    print('='*60)
    
    processor = WeChatArticleProcessor()
    
    try:
        result = processor.extract_article(url)
        
        if 'error' in result:
            print(f"✗ 提取失败: {result['error']}")
            return {
                'url': url,
                'status': 'failed',
                'error': result['error'],
                'title': None,
                'content_length': 0
            }
        
        title = result.get('title', '未找到标题')
        content = result.get('content', '')
        author = result.get('author', '未知')
        image_count = result.get('image_count', 0)
        
        # 验证内容有效性
        if title == "未找到标题" and len(content) < 100:
            print(f"✗ 内容无效: 无法获取文章正文")
            return {
                'url': url,
                'status': 'invalid',
                'error': '无法获取有效内容',
                'title': title,
                'content_length': len(content)
            }
        
        print(f"✓ 提取成功")
        print(f"  标题: {title}")
        print(f"  作者: {author}")
        print(f"  图片: {image_count} 张")
        print(f"  正文: {len(content)} 字符")
        
        # 生成摘要
        summary = processor.generate_summary(result)
        print(f"  摘要: {len(summary)} 字符")
        
        return {
            'url': url,
            'status': 'success',
            'title': title,
            'author': author,
            'content_length': len(content),
            'image_count': image_count,
            'summary_length': len(summary)
        }
        
    except Exception as e:
        print(f"✗ 处理异常: {e}")
        import traceback
        traceback.print_exc()
        return {
            'url': url,
            'status': 'error',
            'error': str(e),
            'title': None,
            'content_length': 0
        }

def process_sequential():
    """顺序处理"""
    print("\n" + "="*60)
    print("顺序处理模式")
    print("="*60)
    
    results = []
    start_time = time.time()
    
    for i, url in enumerate(test_urls):
        result = process_single_article(url, i)
        results.append(result)
    
    elapsed = time.time() - start_time
    return results, elapsed

def process_parallel():
    """并行处理（多线程）"""
    print("\n" + "="*60)
    print("并行处理模式（多线程）")
    print("="*60)
    
    results = []
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(process_single_article, url, i): i 
            for i, url in enumerate(test_urls)
        }
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results.append((index, result))
            except Exception as e:
                print(f"任务 {index+1} 发生异常: {e}")
                results.append((index, {
                    'url': test_urls[index],
                    'status': 'error',
                    'error': str(e)
                }))
    
    # 按原始顺序排序
    results.sort(key=lambda x: x[0])
    results = [r[1] for r in results]
    
    elapsed = time.time() - start_time
    return results, elapsed

def print_summary(results, elapsed_time, mode_name):
    """打印汇总报告"""
    print("\n" + "="*60)
    print(f"{mode_name} - 处理结果汇总")
    print("="*60)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = sum(1 for r in results if r['status'] in ['failed', 'error', 'invalid'])
    
    print(f"总任务数: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"耗时: {elapsed_time:.2f} 秒")
    print(f"平均每个任务: {elapsed_time/len(results):.2f} 秒")
    
    print("\n详细结果:")
    for i, result in enumerate(results):
        status_icon = "✓" if result['status'] == 'success' else "✗"
        title = result.get('title', 'N/A') if result.get('title') else 'N/A'
        error = result.get('error', '')
        
        if result['status'] == 'success':
            print(f"  {status_icon} 任务 {i+1}: {title[:30]}... ({result.get('content_length', 0)} 字符)")
        else:
            print(f"  {status_icon} 任务 {i+1}: {error}")

def main():
    """主函数"""
    print("="*60)
    print("微信公众号文章批量处理测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试链接数: {len(test_urls)}")
    
    # 顺序处理
    seq_results, seq_time = process_sequential()
    print_summary(seq_results, seq_time, "顺序处理")
    
    # 等待一下，避免频率限制
    print("\n等待 5 秒...")
    time.sleep(5)
    
    # 并行处理
    par_results, par_time = process_parallel()
    print_summary(par_results, par_time, "并行处理")
    
    # 对比结果
    print("\n" + "="*60)
    print("性能对比")
    print("="*60)
    print(f"顺序处理耗时: {seq_time:.2f} 秒")
    print(f"并行处理耗时: {par_time:.2f} 秒")
    if par_time > 0:
        speedup = seq_time / par_time
        print(f"加速比: {speedup:.2f}x")
    
    # 验证结果一致性
    print("\n" + "="*60)
    print("结果一致性检查")
    print("="*60)
    
    all_match = True
    for i, (seq, par) in enumerate(zip(seq_results, par_results)):
        if seq['status'] != par['status']:
            print(f"  ✗ 任务 {i+1}: 状态不一致 (顺序:{seq['status']}, 并行:{par['status']})")
            all_match = False
        else:
            print(f"  ✓ 任务 {i+1}: 状态一致 ({seq['status']})")
    
    if all_match:
        print("\n✓ 所有任务结果一致，多线程处理正常！")
    else:
        print("\n✗ 发现结果不一致，需要检查多线程实现！")

if __name__ == "__main__":
    main()
