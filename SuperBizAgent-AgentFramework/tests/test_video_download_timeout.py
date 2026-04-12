#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载动态超时功能回归测试
测试链接：https://www.bilibili.com/video/BV1rGZmYpEQe/
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'agent'))

import unittest
from unittest.mock import Mock, patch
from video_downloader import get_video_duration, calculate_timeout, download_video


class TestVideoDownloadTimeout(unittest.TestCase):
    """测试视频下载动态超时功能"""
    
    def test_calculate_timeout_with_duration(self):
        """测试根据视频时长计算超时时间"""
        # 短视频（5分钟）
        timeout_5min = calculate_timeout(300, base_timeout=300)
        self.assertGreaterEqual(timeout_5min, 300)
        self.assertLessEqual(timeout_5min, 3600)
        print(f"✓ 5分钟视频超时时间: {timeout_5min}秒 ({timeout_5min/60:.1f}分钟)")
        
        # 中等视频（15分钟）
        timeout_15min = calculate_timeout(900, base_timeout=300)
        self.assertGreater(timeout_15min, timeout_5min)
        print(f"✓ 15分钟视频超时时间: {timeout_15min}秒 ({timeout_15min/60:.1f}分钟)")
        
        # 长视频（30分钟）
        timeout_30min = calculate_timeout(1800, base_timeout=300)
        self.assertGreater(timeout_30min, timeout_15min)
        print(f"✓ 30分钟视频超时时间: {timeout_30min}秒 ({timeout_30min/60:.1f}分钟)")
        
        # 超长视频（60分钟）- 应该被限制在最大值
        timeout_60min = calculate_timeout(3600, base_timeout=300)
        self.assertLessEqual(timeout_60min, 3600)
        print(f"✓ 60分钟视频超时时间: {timeout_60min}秒 ({timeout_60min/60:.1f}分钟) - 已限制最大值")
    
    def test_calculate_timeout_without_duration(self):
        """测试无法获取时长时的默认超时"""
        timeout = calculate_timeout(None, base_timeout=300)
        self.assertEqual(timeout, 300)
        print(f"✓ 无法获取时长时使用默认超时: {timeout}秒")
    
    def test_calculate_timeout_bounds(self):
        """测试超时时间的上下限"""
        # 测试下限（短视频）
        timeout_short = calculate_timeout(60, base_timeout=300)  # 1分钟视频
        self.assertGreaterEqual(timeout_short, 300)  # 最少300秒
        print(f"✓ 1分钟视频超时时间（下限测试）: {timeout_short}秒")
        
        # 测试上限（超长视频）
        timeout_long = calculate_timeout(7200, base_timeout=300)  # 2小时视频
        self.assertLessEqual(timeout_long, 3600)  # 最多3600秒
        print(f"✓ 2小时视频超时时间（上限测试）: {timeout_long}秒")
    
    @patch('video_downloader.subprocess.run')
    def test_get_video_duration_success(self, mock_run):
        """测试成功获取视频时长"""
        # 模拟yt-dlp返回视频信息
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"duration": 600, "title": "Test Video"}'
        )
        
        duration = get_video_duration("https://example.com/video")
        
        self.assertIsNotNone(duration)
        self.assertEqual(duration, 600)
        print(f"✓ 成功获取视频时长: {duration}秒")
    
    @patch('video_downloader.subprocess.run')
    def test_get_video_duration_failure(self, mock_run):
        """测试获取视频时长失败"""
        # 模拟yt-dlp失败
        mock_run.return_value = Mock(
            returncode=1,
            stderr='Error: Video not found'
        )
        
        duration = get_video_duration("https://example.com/video")
        
        self.assertIsNone(duration)
        print(f"✓ 获取视频时长失败时返回None")
    
    @patch('video_downloader.subprocess.run')
    def test_get_video_duration_timeout(self, mock_run):
        """测试获取视频时长超时"""
        # 模拟超时
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired(cmd=['yt-dlp'], timeout=30)
        
        duration = get_video_duration("https://example.com/video")
        
        self.assertIsNone(duration)
        print(f"✓ 获取视频时长超时时返回None")


def run_regression_test():
    """运行回归测试"""
    print("\n" + "="*60)
    print("视频下载动态超时功能回归测试")
    print("="*60 + "\n")
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestVideoDownloadTimeout))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
        print("\n现在可以测试实际下载功能：")
        print("测试链接: https://www.bilibili.com/video/BV1rGZmYpEQe/")
        return 0
    else:
        print("\n❌ 测试未通过，请检查失败项")
        return 1


if __name__ == "__main__":
    exit_code = run_regression_test()
    sys.exit(exit_code)
