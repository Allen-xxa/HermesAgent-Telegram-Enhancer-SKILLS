"""
Compression Notifier — sends a Telegram notification when context hygiene
triggers an automatic compression.

Notification format:
    ⟳ 上下文压缩中
    [Lyapunov]
      V=0.0848
      反馈历史=8条
      建议: 系统运行正常
    [相平面]
      轨迹点=42个
      最新x=0.12

Usage in gateway/run.py (inside the _needs_compress block):
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
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Stable paths to engineering cybernetics state files
_STATE_DIR = "/root/.hermes/engineering_cybernetics_study"
_LYAPOV_STATE_FILE = f"{_STATE_DIR}/n3_lyapunov_state.json"
_PHASE_PLANE_STATE_FILE = f"{_STATE_DIR}/n1_phase_plane_state.json"
_P2_PID_STATE_FILE = f"{_STATE_DIR}/p2_pid.json"


def _read_json(path: str) -> dict[str, Any] | None:
    """Read and parse a JSON state file, returning None on any error."""
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _build_cyborg_snapshot() -> list[str]:
    """
    Build a human-readable cybernetics status snapshot from persisted state files.
    Each item in the returned list is a separate paragraph block.
    """
    parts: list[str] = []

    # ── Lyapunov ────────────────────────────────────────────────────────────
    lyap = _read_json(_LYAPOV_STATE_FILE)
    if lyap:
        v_history: list[dict] = lyap.get("V_history", [])
        state_history: list[dict] = lyap.get("state_history", [])
        if v_history:
            v_val: float = v_history[-1].get("V", 0.0) if isinstance(v_history[-1], dict) else float(v_history[-1])
            suggestion: str = "系统运行正常" if v_val < 1.0 else "注意波动"
            parts.append(
                "[Lyapunov]\n"
                f"  V={v_val:.4f}\n"
                f"  反馈历史={len(state_history)}条\n"
                f"  建议: {suggestion}"
            )

    # ── Phase Plane ────────────────────────────────────────────────────────
    pp = _read_json(_PHASE_PLANE_STATE_FILE)
    if pp:
        trajectory: list[dict] = pp.get("trajectory", [])
        if trajectory:
            last_pt: dict = trajectory[-1]
            parts.append(
                "[相平面]\n"
                f"  轨迹点={len(trajectory)}个\n"
                f"  最新x={last_pt.get('x', 0):.2f}"
            )

    # ── PID Preferences ────────────────────────────────────────────────────
    p2 = _read_json(_P2_PID_STATE_FILE)
    if p2:
        prefs: dict = p2.get("current_preferences", {})
        fb: list = p2.get("feedback_history", [])
        if prefs:
            parts.append(
                "[PID偏好]\n"
                f"  风格={prefs.get('style', 0):.3f}\n"
                f"  深度={prefs.get('depth', 0):.3f}\n"
                f"  语气={prefs.get('tone', 0):.3f}\n"
                f"  反馈{len(fb)}次"
            )

    return parts


async def notify_compression_start(
    adapter: Any,
    chat_id: str,
    event_message_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Send a Telegram notification that context compression has started.

    Args:
        adapter:     A TelegramAdapter (or any platform adapter with a `send` method).
        chat_id:     The target chat identifier.
        event_message_id: Optional message ID to reply to.
        metadata:    Optional metadata dict (e.g. {"thread_id": "..."}).
    """
    try:
        cyborg_parts: list[str] = _build_cyborg_snapshot()

        if cyborg_parts:
            notify_text: str = "⟳ 上下文压缩中\n" + "\n".join(cyborg_parts)
        else:
            notify_text = "⟳ 上下文压缩中"

        reply_to: int | None = event_message_id if event_message_id else None

        await adapter.send(
            chat_id,
            notify_text,
            reply_to=reply_to,
            metadata=metadata,
        )
    except Exception as e:
        logger.debug("Compression start notification failed: %s", e)
