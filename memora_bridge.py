# -*- coding: utf-8 -*-
"""
Memora Bridge - 连接 nanobot 与 Memora
"""
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

# 添加 Memora 到路径（作为包导入）
MEMORA_PATH = Path("/Users/rama/.nanobot/workspace")
sys.path.insert(0, str(MEMORA_PATH))

from Memora.src.memory_system import Memora
from Memora.src.models import MemoryNode, SearchResult


class MemoraBridge:
    """
    Memora 桥接器
    让 nanobot 可以方便地读写记忆
    """
    
    def __init__(self):
        self.ms = Memora()
        self._last_search_results: List[SearchResult] = []
    
    def save(self, content: str, title: Optional[str] = None, 
             tags: List[str] = None) -> MemoryNode:
        """
        保存一条记忆
        
        Args:
            content: 记忆内容
            title: 标题（可选，自动提取）
            tags: 标签列表
        
        Returns:
            创建的记忆节点
        """
        # 自动提取标题（前20字）
        if title is None:
            title = content[:20] + "..." if len(content) > 20 else content
        
        # 自动标签
        if tags is None:
            tags = self._auto_tag(content)
        
        node = self.ms.add_memory(
            content=content,
            title=title,
            tags=tags
        )
        
        print(f"[Memory] 已保存: {node.title} (id={node.id})")
        return node
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        搜索相关记忆
        
        Args:
            query: 查询关键词
            top_k: 返回数量
        
        Returns:
            搜索结果列表（已按混合分数排序）
        """
        results = self.ms.search(query, top_k=top_k)
        self._last_search_results = results
        
        print(f"[Memory] 搜索 '{query}' 找到 {len(results)} 条相关记忆")
        for r in results:
            print(f"  [{r.final_score:.3f}] {r.node.title}")
        
        return results
    
    def get_context_memories(self, query: str, max_results: int = 3) -> str:
        """
        获取格式化的记忆上下文，供 LLM 使用
        
        Returns:
            格式化的记忆文本
        """
        results = self.search(query, top_k=max_results)
        
        if not results:
            return ""
        
        context = "\n\n=== 相关历史记忆 ===\n"
        for r in results:
            context += f"\n[{r.node.created.strftime('%Y-%m-%d %H:%M')}] {r.node.title}\n"
            context += f"标签: {', '.join(r.node.tags)} | 重要性: {r.node.pagerank:.3f}\n"
            context += f"内容: {r.node.content[:200]}...\n"
        
        return context
    
    def get_important(self, n: int = 10) -> List[MemoryNode]:
        """获取 PageRank 最高的 n 条重要记忆"""
        all_nodes = self.ms.list_all(limit=1000)
        # 按 pagerank 排序
        sorted_nodes = sorted(all_nodes, key=lambda x: x.pagerank, reverse=True)
        return sorted_nodes[:n]
    
    def build_graph(self, auto_link: bool = True):
        """重建 PageRank 图"""
        self.ms.build_graph(auto_link=auto_link)
        print("[Memory] PageRank 图已重建")
    
    def _auto_tag(self, content: str) -> List[str]:
        """简单自动标签"""
        tags = []
        keywords = {
            "project": ["项目", "project", "实现", "开发"],
            "code": ["代码", "python", "javascript", "bug", "fix"],
            "idea": ["想法", "思路", "概念", "设计"],
            "vrm": ["vrm", "动捕", "mmd", "three.js"],
            "ai": ["ai", "模型", "gpt", "llm", "agent"],
            "memory": ["记忆", "memory", "history"],
        }
        
        content_lower = content.lower()
        for tag, words in keywords.items():
            if any(w in content_lower for w in words):
                tags.append(tag)
        
        return tags if tags else ["general"]


# 单例实例
_memora: Optional[MemoraBridge] = None

def get_memora() -> MemoraBridge:
    """获取 Memora Bridge 实例（懒加载）"""
    global _memora
    if _memora is None:
        _memora = MemoraBridge()
    return _memora


# 便捷函数
def save_to_memora(content: str, title: str = None, tags: List[str] = None):
    """保存记忆"""
    return get_memora().save(content, title, tags)

def search_memories(query: str, top_k: int = 5):
    """搜索记忆"""
    return get_memora().search(query, top_k)

def get_relevant_context(query: str, max_results: int = 3) -> str:
    """获取相关记忆上下文"""
    return get_memora().get_context_memories(query, max_results)
