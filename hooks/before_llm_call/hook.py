# -*- coding: utf-8 -*-
"""
Skill Status Checker Hook
在 LLM 调用前检查质检记录数量，达到阈值时触发修复提醒
"""

import re
from pathlib import Path

from loguru import logger

SKILL_STATUS_PATH = Path("/Users/rama/.nanobot/workspace/Memora/skill/skill_status.md")
THRESHOLD = 5


def _count_quality_checks() -> int:
    """统计 skill_status.md 中的质检记录数量"""
    if not SKILL_STATUS_PATH.exists():
        return 0
    
    content = SKILL_STATUS_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"## 质检记录", content)
    return len(matches)


async def execute(context):
    """Hook 入口函数 - before_llm_call 时执行"""
    
    count = _count_quality_checks()
    
    if count >= THRESHOLD:
        reminder = "（系统提醒：完成用户的任务后开启一个子agent读取 `/Users/rama/.nanobot/workspace/Memora/skill/skill_status.md` 并改进需要优化的 skill, 完成修改后,更新该条记录的skill 已经修复等状态）"
        
        messages = context.get('messages', [])
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                last_msg['content'] = last_msg.get('content', '') + ' ' + reminder
            else:
                # 处理消息对象
                content = getattr(last_msg, 'content', '') or ''
                last_msg.content = content + ' ' + reminder
            logger.info(f"[memora-bridge before-hook] 已追加提醒到最后消息 (records={count})")
        else:
            context['user_input'] = context.get('user_input', '') + ' ' + reminder
            logger.info(f"[memora-bridge before-hook] 已追加提醒到 user_input (records={count})")
    
    return context
