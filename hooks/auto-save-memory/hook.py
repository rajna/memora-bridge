# -*- coding: utf-8 -*-
"""
Memora Bridge - Auto Save Hook (v8 - 使用 MemorySystem.add_memory_from_messages)

## 改进 (v8)
1. **职责分离**: skill 检测、格式化等逻辑移到 MemorySystem
2. **简化代码**: 直接调用 ms.add_memory_from_messages()

## 之前改进 (v7)
1. 清理未使用代码，简化核心流程

## 触发条件
- 对话内容长度 > 10 字符
- 包含重要关键词或内容长度 > 30 字符

## 流程
1. 从 messages 提取当前轮次对话
2. 调用 ms.add_memory_from_messages() 统一处理
3. 自动完成：skill 检测、格式化、标签生成、向量嵌入
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# Memora 路径
MEMORA_PATH = Path("/Users/rama/.nanobot/workspace/Memora")
sys.path.insert(0, str(MEMORA_PATH))

# 简单关键词判断 - 什么内容值得保存
IMPORTANT_KEYWORDS = [
    # 项目相关
    "项目", "project", "架构", "architecture", "设计", "design",
    # 技术决策
    "方案", "solution", "决定", "decision", "选型", "技术",
    # 重要信息
    "重要", "important", "记住", "remember", "备忘", "todo",
    # 问题与解决
    "问题", "issue", "bug", "解决", "fixed", "搞定", "完成",
    # 学习与总结
    "学习", "总结", "笔记", "note", "知识点",
]

def _is_worth_saving(content: str) -> bool:
    """
    判断内容是否值得保存
    
    策略：所有对话都保存（无限制）
    """
    return True


def _extract_current_round(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    从消息列表中提取当前轮次的完整对话（从最近的用户消息开始）
    
    包含：user 消息、assistant 的回复、tool 调用结果
    """
    if not messages:
        return []
    
    # 从后往前找最近的 user 消息位置
    start_idx = 0
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        role = msg.get('role', '') if isinstance(msg, dict) else getattr(msg, 'role', '')
        if role == 'user':
            start_idx = i
            break
    
    # 提取从 start_idx 到末尾的所有消息
    round_messages = messages[start_idx:]
    
    # 转换为标准 dict 格式（nanobot 消息可能是对象）
    standard_messages = []
    for msg in round_messages:
        if isinstance(msg, dict):
            standard_messages.append(msg)
        else:
            # 转换为 dict
            std_msg = {
                'role': getattr(msg, 'role', ''),
                'content': getattr(msg, 'content', None),
            }
            # 处理 tool_calls
            tool_calls = getattr(msg, 'tool_calls', None)
            if tool_calls:
                std_msg['tool_calls'] = tool_calls
            # 处理 tool_call_id
            tool_call_id = getattr(msg, 'tool_call_id', None)
            if tool_call_id:
                std_msg['tool_call_id'] = tool_call_id
            standard_messages.append(std_msg)
    
    return standard_messages


async def execute(context):
    from loguru import logger
    """Hook 入口函数 - on_response 后自动执行"""
    
    try:
        # 获取历史消息
        messages = context.get('messages', [])
        if not messages:
            session = context.get('session')
            if session and hasattr(session, 'messages'):
                messages = list(session.messages)
        
        logger.debug(f"[Memory Hook] 📨 收到 {len(messages)} 条消息")
        
        # 提取当前轮次
        current_round = _extract_current_round(messages)
        if not current_round:
            logger.debug("[Memory Hook] ⏭️ 未找到当前轮次对话")
            return context
        
        logger.debug(f"[Memory Hook] 🔄 当前轮次 {len(current_round)} 条消息")
        
        # 快速检查是否值得保存（避免不必要的 Memora 初始化）
        # 简单拼接检查，不格式化
        quick_check = "\n".join([
            msg.get('content', '') 
            for msg in current_round 
            if msg.get('content')
        ])
        
        logger.debug(f"[Memory Hook] 📝 内容长度: {len(quick_check)} 字符")
        
        if not _is_worth_saving(quick_check):
            logger.debug(f"[Memory Hook] ⏭️ 内容不符合保存条件 (长度={len(quick_check)})")
            return context
        
        logger.debug(f"[Memory Hook] 💾 开始保存...")
        
        # 导入并使用 Memora
        from src.memory_system import Memora
        
        ms = Memora()
        
        # 使用统一方法处理
        node = ms.add_memory_from_messages(
            messages=current_round,
            source="auto-save",
            base_tags=["auto-saved"]
        )
        
        if node:
            logger.info(f"[Memory Hook] ✅ 已保存: {node.title[:40]}... (ID: {node.id})")
        else:
            logger.warning("[Memory Hook] ⚠️ add_memory_from_messages 返回 None")
        
    except Exception as e:
        logger.error(f"[Memory Hook] ❌ 执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return context
