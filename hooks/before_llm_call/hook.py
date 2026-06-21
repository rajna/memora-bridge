# -*- coding: utf-8 -*-
"""
Skill Status Checker Hook + Memory Graph Builder
在 LLM 调用前检查质检记录数量，达到阈值时触发修复提醒
每30次对话turn后自动调用memora的PageRank图谱更新
"""

import re
import sys
from pathlib import Path

from loguru import logger

SKILL_STATUS_PATH = Path("/Users/rama/.nanobot/workspace/Memora/skill/skill_status.md")
THRESHOLD = 35

# 对话计数器配置
TURN_COUNTER_PATH = Path("/Users/rama/.nanobot/workspace/Memora/.turn_counter")
GRAPH_BUILD_INTERVAL = 150  # 每30次对话构建一次图谱

# Memora 路径配置
MEMORA_SRC_PATH = Path("/Users/rama/.nanobot/workspace/Memora/src")
sys.path.insert(0, str(MEMORA_SRC_PATH.parent))


def _count_quality_checks() -> int:
    """统计 skill_status.md 中需要修改的记录数量"""
    if not SKILL_STATUS_PATH.exists():
        return 0
    
    content = SKILL_STATUS_PATH.read_text(encoding="utf-8")
    # 统计需要修改的记录：⚠️ 需优化、⚠️ 修复中、⚠️ 待修复 等状态
    # 以及 failed、poor 等英文状态标记（表格内或独立行）
    patterns = [
        r"⚠️\s*(需优化|修复中|待修复|有问题)",  # 中文状态
        r"\|\s*(failed|poor)\s*\|",  # 表格中的英文状态
        r"\*\*整体质量\*\*:\s*(failed|poor)",  # 独立行的整体质量标记
    ]
    
    total = 0
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        total += len(matches)
    
    return total


def _get_and_increment_turn_count() -> int:
    """
    获取当前对话turn计数并+1
    Returns:
        增加后的计数
    """
    count = 0
    if TURN_COUNTER_PATH.exists():
        try:
            count = int(TURN_COUNTER_PATH.read_text(encoding="utf-8").strip())
        except (ValueError, IOError):
            count = 0
    
    count += 1
    
    # 写入文件
    try:
        TURN_COUNTER_PATH.parent.mkdir(parents=True, exist_ok=True)
        TURN_COUNTER_PATH.write_text(str(count), encoding="utf-8")
    except IOError as e:
        logger.warning(f"[memora-bridge] 写入计数器失败: {e}")
    
    return count


def _build_memory_graph_sync():
    """
    【同步函数】调用Memora的build_graph构建PageRank图谱
    在线程池中执行，不阻塞主事件循环
    """
    try:
        # 动态导入（避免启动时加载失败影响主功能）
        from src.memory_system import MemorySystem
        
        logger.info("[memora-bridge] 开始构建记忆图谱...")
        print("\n🧠 [memora-bridge] 达到30次对话，触发PageRank图谱重建...")
        
        # 初始化记忆系统
        ms = MemorySystem()
        
        # 获取统计
        stats = ms.stats()
        logger.info(f"[memora-bridge] 当前节点数: {stats['total_nodes']}")
        
        # 构建图谱（自动链接 + PageRank计算）
        scores = ms.build_graph(auto_link=True)
        
        logger.info(f"[memora-bridge] 图谱构建完成！共 {len(scores)} 个节点")
        print(f"✅ [memora-bridge] 图谱重建完成！节点: {len(scores)}, 平均PR: {stats['avg_pagerank']:.4f}\n")
        
        return True
        
    except ImportError as e:
        logger.error(f"[memora-bridge] 导入Memora失败: {e}")
        print(f"❌ [memora-bridge] 导入Memora失败: {e}")
        return False
    except Exception as e:
        logger.error(f"[memora-bridge] 构建图谱失败: {e}")
        print(f"❌ [memora-bridge] 构建图谱失败: {e}")
        return False


# 线程池（全局复用）
_graph_executor = None


def _get_executor():
    """获取或创建线程池执行器"""
    global _graph_executor
    if _graph_executor is None:
        from concurrent.futures import ThreadPoolExecutor
        _graph_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="memora-graph")
    return _graph_executor


async def execute(context):
    """Hook 入口函数 - before_llm_call 时执行"""
    import asyncio
    
    # === 1. 对话Turn计数 + 图谱构建 ===
    turn_count = _get_and_increment_turn_count()
    logger.debug(f"[memora-bridge] 当前对话turn: {turn_count}")
    
    # 每30次对话触发一次图谱重建
    if turn_count >= GRAPH_BUILD_INTERVAL:
        # 重置计数器
        try:
            TURN_COUNTER_PATH.write_text("0", encoding="utf-8")
        except IOError as e:
            logger.warning(f"[memora-bridge] 重置计数器失败: {e}")
        
        # 使用线程池在后台执行图谱构建，不阻塞当前请求
        try:
            loop = asyncio.get_event_loop()
            executor = _get_executor()
            # 在线程池中执行（不await，让它后台运行）
            asyncio.create_task(asyncio.wrap_future(
                executor.submit(_build_memory_graph_sync)
            ))
            logger.info(f"[memora-bridge] 已调度图谱构建任务到线程池 (turn={turn_count})")
        except Exception as e:
            logger.error(f"[memora-bridge] 调度图谱任务失败: {e}")
    
    # === 2. Skill质检检查 ===
    count = _count_quality_checks()
    
    if count >= THRESHOLD:
        reminder = "（提醒：完成用户的任务后开启一个子agent读取 `/Users/rama/.nanobot/workspace/Memora/skill/skill_status.md` 精简这个文件 合并 高频问题skill 删除 次要信息,并改进高频率出现问题的 skill, 完成修改后skill_status.md中删除该条记录, 添加修改记录到skill_fixed.md中)"
        
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
