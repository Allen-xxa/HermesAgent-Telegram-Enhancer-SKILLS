---
name: hermes-gateway-enhancer
category: hermes-enhancement
description: Extract inline gateway customizations from Hermes Agent's run.py into modular, upgrade-safe components. Includes Status Bar Footer and Context Compression Notifier. Designed for distribution via HermesAgent-Telegram-Enhancer-SKILLS repo.
version: 1.0.0
author: Allen-xxa / 十二月
tags: [hermes, gateway, refactor, modular, upgrade-safe, telegram, status-bar, compression-notifier]
related_skills: [hermes-inline-patch-extractor, hermes-troubleshooting]
---

# Hermes Gateway Enhancer（Gateway 增强模块解耦方案）

## Overview

将 Hermes Agent 的 `gateway/run.py` 中的两处内联自定义代码块解耦为独立模块，使 Hermes 升级时只需运行一个恢复脚本，无需手动重新修改代码。

**适用场景：** 在 `run.py` 中硬编码了 Status Bar Footer、Compression Notifier 等增强功能的部署环境。

**核心目标：** 每次 Hermes 升级后，**只需运行一个脚本**，即可恢复全部增强功能。

---

## Architecture

```
run.py（官方代码，保持不变）
  ├── import append_status_footer       ← 新增 2 行
  │   └── gateway/status_footer.py     ← 新增独立模块
  └── import notify_compression_start   ← 新增 9 行
      └── gateway/compress_notifier.py ← 新增独立模块

scripts/
  └── hermes-footer-patch               ← 升级恢复脚本
```

### 改造前（内联代码）

```
gateway/run.py  (~10,485 行)
  ├── [约第4658行] 30行内联代码 → Status Bar Footer
  └── [约第4138行] 72行内联代码 → Compression Notifier
```

### 改造后（模块化入口）

```
gateway/run.py  (~10,383 行)  ← 减少约96行
  ├── [约第4658行] 3行: import + append_status_footer(response, agent_result)
  └── [约第4138行] 9行: import + await notify_compression_start(...)

gateway/
  ├── status_footer.py     (57行, 纯函数)
  └── compress_notifier.py (50行, 异步函数, 简洁通知)
```

---

## Prerequisites

- `hermes_agent_core` 容器已部署并运行
- `run.py` 中已有两处内联代码块（可通过特征字符串确认）
- 宿主机可执行 `docker cp` 和 `docker exec`
- Telegram Adapter 已配置（Compression Notifier 需要）

---

## Deployment Steps

### Step 1 — 获取增强模块

在宿主机上：

```bash
git clone https://github.com/Allen-xxa/HermesAgent-Telegram-Enhancer-SKILLS.git
cd HermesAgent-Telegram-Enhancer-SKILLS
```

### Step 2 — 复制模块文件到容器

```bash
CONTAINER=hermes_agent_core
docker cp gateway/status_footer.py ${CONTAINER}:/opt/hermes/gateway/
docker cp gateway/compress_notifier.py ${CONTAINER}:/opt/hermes/gateway/
```

### Step 3 — 修改 run.py（两处）

#### Patch A — Status Bar Footer

在 `run.py` 中找到约 **第 4658 行**，替换：

```
原始（约30行内联代码）：
  short_model = model.split("/")[-1] ...
  ... (生成 footer 字符串)
  response = response + footer

替换为：
  from gateway.status_footer import append_status_footer
  response = append_status_footer(response, agent_result)
```

#### Patch B — Compression Notifier

在 `run.py` 的 `_needs_compress` 块中，找到约 **第 4138 行**，替换：

```
原始（约72行内联代码）：
  _notify_text = "⟳ 上下文压缩中\n" ...
  ... (构建通知，读取 cybernetics 状态)
  await _adapter.send(...)

替换为：
  from gateway.compress_notifier import notify_compression_start

  _hyg_meta = {"thread_id": source.thread_id} if source.thread_id else None
  _adapter = self.adapters.get(source.platform)
  if _adapter and hasattr(_adapter, "send"):
      await notify_compression_start(
          adapter=_adapter,
          chat_id=source.chat_id,
          event_message_id=event.message_id if hasattr(event, "message_id") else None,
          metadata=_hyg_meta,
      )
```

### Step 4 — 重启容器

```bash
docker restart hermes_agent_core
```

---

## Upgrade Recovery

每次升级 Hermes 镜像后：

```bash
cd HermesAgent-Telegram-Enhancer-SKILLS
chmod +x scripts/hermes-footer-patch
./scripts/hermes-footer-patch hermes_agent_core
```

**脚本会执行：**
1. 复制 `gateway/*.py` 到容器
2. 检测 `run.py` 是否已 patch（通过字符串特征）
3. 如果未 patch，替换两处内联代码块
4. 验证 Python 语法
5. 重启容器

**幂等性：** 脚本可重复执行，已 patch 的环境会跳过修改步骤。

---

## Module Reference

### `gateway/status_footer.py`

**函数签名：**
```python
def append_status_footer(response: str, agent_result: dict[str, Any]) -> str
```

**功能：** 在 agent 文本回复末尾追加上下文使用状态条。

**格式：**
```
⚕ MiniMax-M2.7 │ 47K/204.8K │ [██░░░░░░░░] 23%
```

**依赖字段：**

| 字段 | 来源 key | 数据来源 | 何时写入 |
|------|----------|---------|---------|
| 模型名称 | `agent_result["model"]` | LLM API 响应 → `run_conversation()` → `_run_agent()` → `run.py` | `run_agent.py` 从 API 响应中提取 |
| 已用 tokens | `agent_result["last_prompt_tokens"]` | 同上，来自 `usage.prompt_tokens` | API 每次响应时更新，同时持久化到 `session_entry.last_prompt_tokens` |
| 总上下文 | `agent_result["context_length"]` | `get_model_context_length(model)` 查表（`agent/model_metadata.py`） | `run.py` 第 3793 行在 `_run_agent` 调用前解析；Footer 函数内 fallback 调用 |

**数据流完整链路：**

```
LLM API Response
  └── usage.prompt_tokens / usage.total_tokens
      └── run_conversation() 返回 agent_result dict
          ├── agent_result["model"] = "minimax-cn/MiniMax-M2.7"
          ├── agent_result["last_prompt_tokens"] = 47123
          └── agent_result["context_length"] = 204800  ← 由 get_model_context_length(model) 查表得到

run.py:4600
  └── append_status_footer(response, agent_result)
        ├── agent_result["model"]           → "minimax-cn/MiniMax-M2.7"
        ├── agent_result["last_prompt_tokens"] → 47123
        └── agent_result["context_length"]    → 204800
```

**注意：** `agent_result` 本身不直接包含 `context_length` 时，Footer 函数会从 `agent.model_metadata.get_model_context_length(model)` 查表获取。`context_length` 是**模型的最大上下文窗口**（固定值，如 MiniMax-M2.7 = 204800），不是当前已用量。

**容错：** 任何字段缺失均不抛异常，原样返回原始 response。

---

### `gateway/compress_notifier.py`

**函数签名：**
```python
async def notify_compression_start(
    adapter: Any,
    chat_id: str,
    event_message_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None
```

**发送内容：**
```
⟳ 上下文压缩中…
```

简洁明了，仅告知用户当前正在执行上下文压缩操作。

**设计原则：** 此模块只负责通知用户"正在压缩"，不涉及任何系统内部状态（如 cybernetics）。系统内部状态通过 `cybernetics_middleware` 注入到 Agent 的 system prompt，是给 Agent 自己看的，不是给用户看的。

---

## Pitfalls

### 1. 精确匹配 old_string
`memory` 工具的 `replace` 需要精确匹配 old_string。`hermes-footer-patch` 脚本使用正则表达式，匹配更宽松，但仍建议先在测试环境验证。

### 2. Container vs Repo 版本差异
容器内 `run.py`（~10,485 行）可能与 GitHub 仓库（~10,380 行）不完全一致。patch 脚本通过特征字符串匹配，而非固定行号，兼容两种版本。

### 3. 复制后权限
`docker cp` 会保留文件权限，但如果容器内 Python 解释器缺少执行权限，确保：
```bash
docker exec ${CONTAINER} chmod 644 /opt/hermes/gateway/status_footer.py
docker exec ${CONTAINER} chmod 644 /opt/hermes/gateway/compress_notifier.py
```

---

## Verification

### 功能验证

发送任意消息给 Bot，检查回复底部是否出现状态条。

### Patch 脚本验证

```bash
# 检查 run.py 中是否包含我们的 import
docker exec ${CONTAINER} grep -n "append_status_footer" /opt/hermes/gateway/run.py
docker exec ${CONTAINER} grep -n "notify_compression_start" /opt/hermes/gateway/run.py

# 应该看到两行输出（import 行和 call 行）
```

### 模块语法验证

```bash
docker exec ${CONTAINER} python3 -c "
from gateway.status_footer import append_status_footer
from gateway.compress_notifier import notify_compression_start
print('OK: both modules imported successfully')
"
```

---

## Context Window Impact

|| 改动 | 行数变化 | Context 影响 |
||------|---------|-------------||
|| `run.py` 删除内联代码 | -96 行 | 略微减少 ||
|| `status_footer.py` 新增 | +57 行 | 略微增加 ||
|| `compress_notifier.py` 新增 | +50 行 | 略微增加 ||
|| **净变化** | **+11 行** | 可忽略不计 ||
