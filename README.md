# HermesAgent-Telegram-Enhancer-SKILLS

> Hermes Agent Telegram 增强技能包 — 让其他 Agent 也能一键部署同样的增强功能

---

## 🎯 这个仓库包含什么

两个 Hermes Agent 的 **gateway 层增强模块**，已从 `run.py` 解耦为独立文件：

| 模块 | 文件 | 功能 |
|------|------|------|
| **Status Bar Footer** | `gateway/status_footer.py` | 在每条回复底部追加 `⚕ MiniMax-M2.7 │ 47K/204.8K │ [██░░░░░░░░] 23%` |
| **Compression Notifier** | `gateway/compress_notifier.py` | 上下文压缩时自动发送 Telegram 通知，包含系统状态快照 |

---

## 📋 前提条件

- Hermes Agent 已部署并运行中
- Telegram Adapter 已配置（能发送消息）
- 工程控制论状态文件已初始化（可选，通知模块会优雅降级）

---

## 🚀 部署步骤

### Step 1 — 拉取模块文件

登录到运行 `hermes_agent_core` 容器的宿主机，执行：

```bash
# 克隆仓库
git clone https://github.com/Allen-xxa/HermesAgent-Telegram-Enhancer-SKILLS.git
cd HermesAgent-Telegram-Enhancer-SKILLS

# 复制模块文件到容器 gateway 目录
docker cp gateway/status_footer.py hermes_agent_core:/opt/hermes/gateway/
docker cp gateway/compress_notifier.py hermes_agent_core:/opt/hermes/gateway/
```

### Step 2 — 修改 run.py（两处）

找到 `gateway/run.py`，按下面描述替换对应代码块。

#### 修改点 A：Status Bar Footer（约第 4658 行附近）

**原来（约 30 行内联代码）：**
```python
# ... 约30行内联代码，生成 footer 字符串并追加到 response ...
```

**替换为（仅 3 行）：**
```python
from gateway.status_footer import append_status_footer
# 在 return response 之前追加 footer
response = append_status_footer(response, agent_result)
```

#### 修改点 B：Compression Notifier（约第 4138 行附近）

**找到 `_needs_compress` 块中发送通知的位置（约 72 行内联代码）：**
```python
# ... 约72行内联代码，构建并发送压缩通知 ...
```

**替换为（仅 9 行）：**
```python
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

### Step 3 — 重启容器

```bash
docker restart hermes_agent_core
```

### Step 4 — 验证

发送任意消息给 Bot，观察回复底部是否出现状态条：
```
⚕ MiniMax-M2.7 │ 47K/204.8K │ [██░░░░░░░░] 23%
```

---

## 🔧 一键恢复脚本（升级 Hermes 后使用）

```bash
# 在宿主机上执行
cd HermesAgent-Telegram-Enhancer-SKILLS
chmod +x scripts/hermes-footer-patch
./scripts/hermes-footer-patch hermes_agent_core
```

脚本会自动：
1. 复制两个 `.py` 模块到容器
2. 找到 `run.py` 中需要替换的代码块（通过特征字符串匹配）
3. 替换为 import + call 入口
4. 验证 Python 语法
5. 重启容器

---

## 📁 文件结构

```
HermesAgent-Telegram-Enhancer-SKILLS/
├── README.md                          ← 你在这里
├── SKILL.md                           ← Hermes Skill 定义文档
├── gateway/
│   ├── status_footer.py               ← Status Bar Footer 模块（纯函数）
│   └── compress_notifier.py           ← Compression Notifier 模块（异步）
└── scripts/
    └── hermes-footer-patch             ← 升级恢复脚本
```

---

## 🔬 模块详解

### Status Bar Footer (`status_footer.py`)

**函数：** `append_status_footer(response, agent_result) -> str`

- 输入：`agent_result["model"]`、`agent_result["last_prompt_tokens"]`、`agent_result["context_length"]`
- 输出：在 response 末尾追加 `⚕ {model} │ {tokens}/{ctx} │ [{bar}] {pct}%`
- 容错：任何字段缺失都不会抛异常，默默降级

### Compression Notifier (`compress_notifier.py`)

**函数：** `notify_compression_start(adapter, chat_id, event_message_id, metadata)`

- 发送 Telegram 消息：`⟳ 上下文压缩中`
- 附加当前工程控制论状态快照（如果有）：
  - **Lyapunov V 值**：系统稳定性指标
  - **相平面轨迹**：收敛状态
  - **PID 偏好**：当前参数风格
- 状态文件路径：`/root/.hermes/engineering_cybernetics_study/`

---

## ⚠️ 常见问题

**Q: 升级 Hermes 后功能消失了？**  
A: 运行 `scripts/hermes-footer-patch` 即可一键恢复。

**Q: 提示 `No module named 'gateway.status_footer'`？**  
A: 确保 `status_footer.py` 和 `compress_notifier.py` 已复制到容器的 `/opt/hermes/gateway/` 目录。

**Q: 通知没有发到 Telegram？**  
A: 检查工程控制论状态文件是否存在：`docker exec hermes_agent_core ls /root/.hermes/engineering_cybernetics_study/`

---

## 📝 License

MIT — 随便用，随便改～
