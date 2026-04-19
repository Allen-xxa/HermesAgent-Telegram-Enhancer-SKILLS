"""
Compression Notifier — sends a Telegram notification when context hygiene
triggers an automatic compression.

Notification format:
    ⟳ 上下文压缩中…

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

import logging
from typing import Any

logger = logging.getLogger(__name__)


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
        notify_text: str = "⟳ 上下文压缩中…"

        reply_to: int | None = event_message_id if event_message_id else None

        await adapter.send(
            chat_id,
            notify_text,
            reply_to=reply_to,
            metadata=metadata,
        )
    except Exception as e:
        logger.debug("Compression start notification failed: %s", e)