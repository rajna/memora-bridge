# -*- coding: utf-8 -*-
"""
Memora Bridge Server - 简化版
通过 subprocess 调用 Memora
"""
import subprocess
import json
import sys
from pathlib import Path

MEMORY_SYSTEM_PATH = Path("/Users/rama/.nanobot/workspace/Memora")


def search(query: str, top_k: int = 5):
    """搜索记忆"""
    cmd = [
        sys.executable, "-c",
        f"""
import sys
sys.path.insert(0, '{MEMORY_SYSTEM_PATH}')
exec(open('{MEMORY_SYSTEM_PATH}/src/memory_system.py').read())
        """
    ]
    # 简化：直接返回 web 界面链接
    print(f"🔍 搜索 '{query}' - 请查看: http://localhost:5001")
    print(f"   或在浏览器打开并搜索: {query}")


def save(title: str, content: str, tags=None):
    """保存记忆 - 写入到特殊文件，由 heartbeat 批量导入"""
    if tags is None:
        tags = []
    
    # 写入待导入队列
    queue_file = MEMORY_SYSTEM_PATH / "_pending_imports.jsonl"
    
    entry = {
        "title": title,
        "content": content,
        "tags": tags,
        "timestamp": str(datetime.now())
    }
    
    with open(queue_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"💾 已排队保存: {title}")
    print(f"   将在下次 heartbeat 时导入到记忆系统")


# 临时方案：直接使用 web 界面
print("""
🧠 Memory System 已运行
═══════════════════════════════════════
Web 界面: http://localhost:5001

快速操作:
1. 打开浏览器访问上面链接
2. 使用搜索框查找记忆
3. 按标签筛选

待实现:
- [ ] 自动保存对话到队列
- [ ] 对话前自动检索相关记忆
- [ ] Heartbeat 批量导入
""")
