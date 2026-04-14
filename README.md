# Memora Bridge

连接 nanobot 与 Memora 记忆系统的桥梁，实现对话自动记录与检索。

## 功能特性

- ✅ **自动保存** - 对话结束后自动判断是否值得保存
- ✅ **直接写入** - 调用 Memora API 直接持久化，无需队列
- ✅ **向量嵌入** - 自动生成 embedding 支持语义检索
- ✅ **PageRank 图** - 自动构建记忆关联网络

## 架构

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  nanobot    │────▶│  Hook 触发   │────▶│  memora_bridge  │
│  对话结束   │     │ 智能判断     │     │ .save()         │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                   │
                                                   ▼
                                          ┌─────────────────┐
                                          │  Memora/data/   │
                                          │  YYYY/MM/DD/    │
                                          │  直接持久化      │
                                          └─────────────────┘
```

## 快速开始

### 自动保存（默认开启）

Hook 自动捕获对话并直接保存：

```
用户: "我们要设计一个 Memora 集成方案..."
      ↓
Hook: 检测关键词 "方案" + 长度 > 100 → 直接调用 save()
      ↓
Memora: 生成 embedding → 保存到 data/2026/04/14/xxx.md
```

### 手动保存

```python
from skills.memora_bridge import save_to_memora

save_to_memora(
    content="用户讨论了新的架构设计...",
    title="架构设计讨论",
    tags=["architecture", "design"]
)
```

### 检索记忆

```python
from skills.memora_query import search_memories

results = search_memories("那个 Memora 方案", top_k=5)
```

## 配置

编辑 `hooks/auto-save-memory/hook.py`：

```python
MIN_CONTENT_LENGTH = 100  # 最小保存长度
IMPORTANT_KEYWORDS = [
    "项目", "project", "问题", "bug",
    "方案", "设计", "架构", "优化"
]
```

## 文件结构

```
memora-bridge/
├── SKILL.md                 # 技能说明
├── README.md               # 本文档
├── memora_bridge.py        # 核心桥接逻辑（直接保存）
└── hooks/
    ├── auto-save-memory/   # 自动保存 Hook
    │   ├── hook.md
    │   └── hook.py
    └── before_llm_call/    # Skill 质检 Hook
        ├── hook.md
        └── hook.py
```

## 依赖

- Memora 记忆系统（需单独部署）
- `memora_query` skill（用于检索）

## 相关链接

- Memora Web: http://localhost:5001
- 记忆存储: `Memora/data/YYYY/MM/DD/`
