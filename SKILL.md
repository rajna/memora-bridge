---
name: memora-bridge
description: 连接 nanobot 与 Memora 的桥梁，实现对话自动记录。
always: true
---


## 状态
✅ **可用** - 基础保存功能已测试通过
✅ **自动保存** - on_response hook 已配置

## 快速开始

### 方式1：自动保存（推荐）
已配置 `on_response` hook，每次对话后自动判断并保存重要内容：

```
对话结束 → Hook 触发 → 智能判断 → 写入队列 → Heartbeat 导入
```

**智能判断条件：**
- 对话长度 > 100 字符
- 包含关键词：项目、问题、方案、学习、bug 等
- 或对话长度 > 300 字符（视为有实质内容）

### 方式2：手动保存

```python
from skills.memora_bridge import save_to_memora

# 手动保存重要对话
save_memory(
    content="用户询问了 Memory System 的集成方案...",
    title="Memory System 集成讨论", 
    tags=["architecture", "Memora"]
)
```

## 工作流程

### 自动保存流程
```
1. 用户对话结束
   ↓
2. on_response Hook 触发
   ↓
3. 提取最近3轮对话
   ↓
4. 智能判断是否值得保存
   ↓
5. 生成标题 + 自动打标签
   ↓
6. 写入 _pending_queue.jsonl
   ↓
7. Heartbeat (30分钟) 调用 process_queue.py
   ↓
8. 导入到 Memora/data/
   ↓
9. 可在 http://localhost:5001 查看
```

### 手动保存流程
```
1. nanobot 调用 save_memory()
   ↓
2. 写入 _pending_queue.jsonl
   ↓
3. Heartbeat 调用 process_queue.py
   ↓
4. 导入到 Memora/data/
   ↓
5. 可在 http://localhost:5001 查看
```

## 文件位置

### Hook 自动保存
- Hook 配置: `skills/memora-bridge/hooks/auto-save-memory/hook.md`
- Hook 逻辑: `skills/memora-bridge/hooks/auto-save-memory/hook.py`

### 核心模块
- 队列文件: `Memora/_pending_queue.jsonl`
- 处理脚本: `Memora/tools/process_queue.py`
- 记忆存储: `Memora/data/YYYY/MM/DD/`
- Web 查看: http://localhost:5001

## 配置 Hook

编辑 `hooks/auto-save-memory/hook.py` 可调整：

```python
MIN_CONTENT_LENGTH = 100  # 最小保存长度
IMPORTANT_KEYWORDS = [    # 重要关键词
    "项目", "project", "问题", "bug", ...
]
```

## 下一步

- [x] 对话后自动保存 (on_response Hook) ✅
- [ ] 对话前自动检索相关记忆
- [ ] 基于 PageRank 的智能推荐
- [ ] 更精准的自动标签生成
