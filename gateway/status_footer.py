"""
Status Bar Footer — appends a compact context-usage line to each agent response.

Format: ⚕ <model> │ <tokens>/<context_len> │ [<bar>] <pct>%
Example: ⚕ MiniMax-M2.7 │ 47K/204.8K │ [██░░░░░░░░] 23%

Usage in gateway/run.py:
    from gateway.status_footer import append_status_footer
    response = append_status_footer(response, agent_result)
"""

from typing import Any


def _fmt_toks(t: int) -> str:
    """Format token count with K suffix for readability."""
    if t >= 1000:
        return f"{t / 1000:.1f}K".replace(".0K", "K")
    return str(t)


def append_status_footer(response: str, agent_result: dict[str, Any]) -> str:
    """
    Append a compact status footer to the agent's text response.

    Shows: model name + context token usage + progress bar.
    Never raises — errors are silently swallowed so the footer
    can never break a real response.
    """
    try:
        model: str = agent_result.get("model", "unknown")
        tokens: int = agent_result.get("last_prompt_tokens", 0) or 0

        # Resolve context_length
        ctx_len: int | None = agent_result.get("context_length")
        if not ctx_len:
            from agent.model_metadata import get_model_context_length

            ctx_len = get_model_context_length(model) if model else 204_800

        # Shorten provider prefix if present (e.g. "minimax-cn/MiniMax-M2.7" → "MiniMax-M2.7")
        short_model: str = model.split("/")[-1] if "/" in model else (model or "?")

        # Token strings
        tok_str: str = _fmt_toks(tokens)
        ctx_str: str = _fmt_toks(ctx_len)

        # Progress bar (10 chars: █ = filled, ░ = empty)
        pct: float = min(100.0, tokens / ctx_len * 100) if ctx_len else 0.0
        filled: int = int(pct / 10)
        bar: str = "█" * filled + "░" * (10 - filled)

        footer: str = f"\n\n⚕ {short_model} │ {tok_str}/{ctx_str} │ [{bar}] {pct:.0f}%"
        return response + footer

    except Exception:
        return response
