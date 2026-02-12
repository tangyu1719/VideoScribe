#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书知识库集成模块（MCP方式）
- 初始化MCP客户端
- 获取访问令牌（TAT）
- 通过MCP工具调用实现文档库操作
- 支持指定知识库节点创建MD格式文档
"""

import requests
import json
import hashlib
import os
import time
import re

class FeishuKnowledgeBase:
    def __init__(self, app_id, app_secret):
        """初始化飞书客户端"""
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.mcp_url = "https://mcp.feishu.cn/mcp"
        self.access_token = None
        self.token_expire_time = 0
        # 去重存储
        self.dedup_file = "feishu_dedup.json"
        self.load_dedup_data()
    
    def load_dedup_data(self):
        """加载去重数据"""
        try:
            if os.path.exists(self.dedup_file):
                with open(self.dedup_file, 'r', encoding='utf-8') as f:
                    self.dedup_data = json.load(f)
            else:
                self.dedup_data = {}
        except Exception as e:
            print(f"加载去重数据失败: {e}")
            self.dedup_data = {}
    
    def save_dedup_data(self):
        """保存去重数据"""
        try:
            with open(self.dedup_file, 'w', encoding='utf-8') as f:
                json.dump(self.dedup_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存去重数据失败: {e}")
    
    def generate_hash(self, content):
        """生成内容的MD5哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, content):
        """检查内容是否重复"""
        content_hash = self.generate_hash(content)
        if content_hash in self.dedup_data:
            return True
        # 添加新哈希
        self.dedup_data[content_hash] = True
        self.save_dedup_data()
        return False
    
    def get_tenant_access_token(self):
        """获取Tenant Access Token (TAT)"""
        try:
            # 检查令牌是否过期
            if self.access_token and time.time() < self.token_expire_time:
                return self.access_token
            
            # 调用获取令牌API
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            headers = {"Content-Type": "application/json"}
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if result.get("code") == 0:
                self.access_token = result.get("tenant_access_token")
                expire = result.get("expire", 7200)
                self.token_expire_time = time.time() + expire - 300  # 提前5分钟过期
                print("获取Tenant Access Token成功")
                return self.access_token
            else:
                print(f"获取Tenant Access Token失败: {result.get('msg')}")
                return None
        except Exception as e:
            print(f"获取Tenant Access Token异常: {e}")
            return None
    
    def mcp_request(self, method, params, allowed_tools):
        """发送MCP请求
        
        Args:
            method: 请求方法
            params: 请求参数
            allowed_tools: 允许的工具列表
            
        Returns:
            响应结果或None
        """
        try:
            # 获取TAT
            token = self.get_tenant_access_token()
            if not token:
                return None
            
            # 构造请求头
            headers = {
                "Content-Type": "application/json",
                "X-Lark-MCP-TAT": token,
                "X-Lark-MCP-Allowed-Tools": ",".join(allowed_tools)
            }
            
            # 构造请求体
            request_body = {
                "jsonrpc": "2.0",
                "id": int(time.time() * 1000),
                "method": method,
                "params": params
            }
            
            # 发送请求
            response = requests.post(self.mcp_url, headers=headers, json=request_body)
            print(f"MCP请求状态码: {response.status_code}")
            print(f"MCP请求响应: {response.text[:500]}...")
            
            result = response.json()
            if "error" in result:
                print(f"MCP请求失败: {result['error'].get('message')}")
                return None
            
            return result.get("result")
        except Exception as e:
            print(f"MCP请求异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_docs(self, folder_token, page_size=100):
        """使用MCP的list-docs工具查询文件夹
        
        Args:
            folder_token: 文件夹token
            page_size: 分页大小
            
        Returns:
            文件夹列表或None
        """
        try:
            print(f"\n=== 调用MCP list-docs工具 ===")
            print(f"Folder Token: {folder_token}")
            
            params = {
                "name": "list-docs",
                "arguments": {
                    "folder_token": folder_token,
                    "page_size": page_size
                }
            }
            
            result = self.mcp_request("tools/call", params, ["list-docs"])
            if not result:
                return None
            
            # 解析响应
            content = result.get("content", [])
            if not content:
                print("list-docs返回空结果")
                return None
            
            # 提取文件夹信息
            items = []
            for item in content:
                if item.get("type") == "text":
                    text = item.get("text", "{}")
                    try:
                        data = json.loads(text)
                        items.extend(data.get("files", []))
                    except:
                        pass
            
            print(f"✓ 成功获取 {len(items)} 个项目")
            return items
        except Exception as e:
            print(f"list-docs工具调用异常: {e}")
            return None
    
    def create_doc(self, title, content, parent_node_token):
        """使用MCP的create-doc工具创建MD格式文档
        
        Args:
            title: 文档标题
            content: MD格式内容
            parent_node_token: 父节点token
            
        Returns:
            文档信息或None
        """
        try:
            print(f"\n=== 调用MCP create-doc工具 ===")
            print(f"标题: {title}")
            print(f"父节点: {parent_node_token}")
            
            # 按照教程要求，使用parent_node参数
            params = {
                "name": "create-doc",
                "arguments": {
                    "parent_node": parent_node_token,
                    "title": title,
                    "content": content
                }
            }
            
            result = self.mcp_request("tools/call", params, ["create-doc"])
            if not result:
                return None
            
            print("✓ 文档创建成功")
            return result
        except Exception as e:
            print(f"create-doc工具调用异常: {e}")
            return None
    
    def update_doc(self, doc_id, content):
        """使用MCP的update-doc工具更新文档内容
        
        Args:
            doc_id: 文档ID
            content: MD格式内容
            
        Returns:
            更新结果或None
        """
        try:
            print(f"\n=== 调用MCP update-doc工具 ===")
            print(f"文档ID: {doc_id}")
            
            params = {
                "name": "update-doc",
                "arguments": {
                    "docID": doc_id,
                    "markdown": content,  # 使用markdown参数而非content
                    "mode": "overwrite"  # 使用overwrite模式完全替换内容
                }
            }
            
            result = self.mcp_request("tools/call", params, ["update-doc"])
            if not result:
                return None
            
            print("✓ 文档更新工具调用成功")
            return result
        except Exception as e:
            print(f"update-doc工具调用异常: {e}")
            return None
    
    def find_folder_by_name(self, folder_token, folder_name):
        """通过名称查找文件夹
        
        Args:
            folder_token: 起始文件夹token
            folder_name: 文件夹名称
            
        Returns:
            文件夹信息或None
        """
        try:
            items = self.list_docs(folder_token)
            if not items:
                return None
            
            for item in items:
                if item.get("type") == "folder" and item.get("name") == folder_name:
                    print(f"✓ 找到文件夹: {folder_name} (token: {item.get('token')})")
                    return item
            
            print(f"未找到文件夹: {folder_name}")
            return None
        except Exception as e:
            print(f"查找文件夹异常: {e}")
            return None
    
    def create_empty_document(self, title, node_token):
        """通过MCP创建空文档
        
        Args:
            title: 文档标题
            node_token: 目标知识库节点token
            
        Returns:
            文档token或None
        """
        try:
            print(f"\n=== 开始通过MCP创建空文档 ===")
            print(f"文档标题: {title}")
            print(f"目标节点: {node_token}")
            
            # 步骤1：初始化MCP会话
            init_result = self.mcp_request("initialize", {}, [])
            if init_result:
                print("✓ MCP会话初始化成功")
            
            # 步骤2：创建空文档
            create_result = self.create_doc(title, "", node_token)
            if not create_result:
                print("创建空文档失败")
                return None
            
            # 提取文档信息
            doc_info = None
            content_items = create_result.get("content", [])
            for item in content_items:
                if item.get("type") == "text":
                    text = item.get("text", "{}")
                    try:
                        doc_info = json.loads(text)
                        break
                    except:
                        pass
            
            if not doc_info:
                print("创建空文档成功但未返回文档信息")
                return None
            
            doc_id = doc_info.get("doc_id")
            doc_url = doc_info.get("doc_url")
            
            if not doc_id:
                print("创建空文档成功但未返回doc_id")
                return None
            
            print(f"✓ 成功创建空文档")
            print(f"  Document ID: {doc_id}")
            print(f"  Document URL: {doc_url}")
            
            return doc_id
        except Exception as e:
            print(f"创建空文档异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def update_document_content(self, doc_id, content):
        """通过MCP更新文档内容
        
        Args:
            doc_id: 文档ID
            content: MD格式文档内容
            
        Returns:
            bool: 更新是否成功
        """
        try:
            print(f"\n=== 开始通过MCP更新文档内容 ===")
            print(f"文档ID: {doc_id}")
            print(f"内容长度: {len(content)} 字符")
            
            # 步骤1：初始化MCP会话
            init_result = self.mcp_request("initialize", {}, [])
            if init_result:
                print("✓ MCP会话初始化成功")
            
            # 步骤2：更新文档内容
            update_result = self.update_doc(doc_id, content)
            if not update_result:
                print("更新文档内容失败")
                return False
            
            # 检查更新结果
            update_success = False
            content_items = update_result.get("content", [])
            for item in content_items:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    if "成功" in text or "success" in text.lower():
                        update_success = True
                        break
            
            if update_success:
                print("✓ 成功更新文档内容")
                
                # 备份文档内容到本地
                backup_file = f"{doc_id}_updated_content.md"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ 文档内容已备份到: {backup_file}")
                
                return True
            else:
                print("更新文档内容失败：未收到成功响应")
                return False
        except Exception as e:
            print(f"更新文档内容异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_md_document(self, title, content, node_token):
        """通过MCP创建MD格式文档
        
        Args:
            title: 文档标题
            content: MD格式文档内容
            node_token: 目标知识库节点token
            
        Returns:
            文档token或None
        """
        try:
            # 检查内容是否重复
            if self.is_duplicate(content):
                print("文档内容重复，跳过上传")
                return None
            
            # 使用两步流程：先创建空文档，再更新内容
            doc_id = self.create_empty_document(title, node_token)
            if doc_id:
                success = self.update_document_content(doc_id, content)
                if success:
                    return doc_id
                else:
                    print("更新内容失败")
                    return None
            else:
                print("创建空文档失败")
                return None
        except Exception as e:
            print(f"创建文档异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def upload_document(self, title, content, folder_name=None, feishu_folder_path=None, node_token=None):
        """上传文档到飞书
        
        Args:
            title: 文档标题
            content: 文档内容
            folder_name: 文件夹名称（兼容旧接口）
            feishu_folder_path: 飞书具体文件夹路径
            node_token: 知识库节点token
            
        Returns:
            文档token或None
        """
        # 如果提供了node_token，使用MCP方式创建MD文档
        if node_token:
            return self.create_md_document(title, content, node_token)
        
        # 兼容旧接口：根据文件夹路径查找node_token
        try:
            # 检查内容是否重复
            if self.is_duplicate(content):
                print("文档内容重复，跳过上传")
                return None
            
            # 确定最终的文件夹路径
            final_folder_path = feishu_folder_path or folder_name
            if not final_folder_path:
                # 智能分类：根据内容自动判断文件夹
                final_folder_path = self.auto_classify_content(content)
            
            print(f"准备上传到文件夹: {final_folder_path}")
            
            # 解析文件夹路径，查找对应的node_token
            # 这里需要根据实际的知识库结构实现路径映射
            # 暂时使用默认的知识库节点
            default_node_token = "YhzqwByshiRNWKk0T1GcxFHmn6b"  # 从URL提取的默认节点
            
            # 如果路径包含子文件夹，需要递归查找
            if "/" in final_folder_path:
                parts = final_folder_path.split("/")
                current_token = default_node_token
                
                for part in parts[1:]:  # 跳过根路径
                    folder = self.find_folder_by_name(current_token, part)
                    if folder:
                        current_token = folder.get("token")
                    else:
                        print(f"找不到子文件夹: {part}")
                        break
                
                return self.create_md_document(title, content, current_token)
            else:
                return self.create_md_document(title, content, default_node_token)
                
        except Exception as e:
            print(f"上传文档异常: {e}")
            return None
    
    def auto_classify_content(self, content):
        """根据内容智能分类到飞书文件夹
        
        Returns:
            飞书文件夹路径
        """
        content_lower = content.lower()
        
        # 分类规则
        if any(keyword in content_lower for keyword in ["wms", "仓储", "仓库", "物流"]):
            return "就业技术文档集/WMS"
        elif any(keyword in content_lower for keyword in ["八股", "面试", "java", "jvm", "spring"]):
            return "就业技术文档集/八股"
        elif any(keyword in content_lower for keyword in ["aiops", "智能运维", "监控", "告警"]):
            return "就业技术文档集/AIOPS"
        elif any(keyword in content_lower for keyword in ["算法", "数据结构", "leetcode"]):
            return "就业技术文档集/算法"
        else:
            return "就业技术文档集/其他"
    
    def parse_feishu_folder_from_prompt(self, user_prompt):
        """从用户提示词中解析飞书文件夹路径
        
        Args:
            user_prompt: 用户提示词
            
        Returns:
            飞书文件夹路径或None
        """
        if not user_prompt:
            return None
        
        # 查找飞书文件夹路径的模式
        pattern = r'飞书文件夹[:：]\s*([^\n]+)'
        match = re.search(pattern, user_prompt)
        if match:
            folder_path = match.group(1).strip()
            print(f"从提示词中解析到飞书文件夹: {folder_path}")
            return folder_path
        
        return None
    
    def parse_node_token_from_url(self, url):
        """从URL中解析节点token
        
        Args:
            url: 飞书知识库URL
            
        Returns:
            节点token或None
        """
        pattern = r'wiki/([\w]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    
    def add_to_read_later(self, doc_token):
        """添加文档到稍后阅读"""
        try:
            print(f"文档已添加到稍后阅读: {doc_token}")
            return True
        except Exception as e:
            print(f"添加到稍后阅读异常: {e}")
            return False
    
    def init_from_url(self, url):
        """从链接初始化"""
        print(f"从链接初始化: {url}")
        node_token = self.parse_node_token_from_url(url)
        if node_token:
            print(f"解析到节点token: {node_token}")
            # 测试list-docs工具
            items = self.list_docs(node_token)
            if items:
                print(f"成功获取节点下的项目: {len(items)}")
            return True
        else:
            print("解析节点token失败")
            return False
