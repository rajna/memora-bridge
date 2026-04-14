---
name: skill-status-checker
description: |
  在 before_llm_call 时检查 skill_status.md 的质检记录数量。
  当累计达到 5 条时，在消息上下文末尾插入提醒，触发 skill 自动修复流程。
trigger:
  event: before_llm_call
  priority: 10
---
