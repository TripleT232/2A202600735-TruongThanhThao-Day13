from __future__ import annotations

import os
from typing import Any


def tracing_enabled() -> bool:
    return bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))


class _DummyContext:
    def update_current_trace(self, **kwargs: Any) -> None:
        return None

    def update_current_observation(self, **kwargs: Any) -> None:
        return None


def _dummy_observe(func: Any = None, **_kwargs: Any):
    def decorator(fn: Any) -> Any:
        return fn

    if func is not None:
        return func
    return decorator


try:
    from langfuse import get_client, observe as _observe

    def observe(*args: Any, **kwargs: Any):
        return _observe(*args, **kwargs)

    class _LangfuseContextAdapter:
        def update_current_trace(self, **kwargs: Any) -> None:
            if tracing_enabled():
                get_client().update_current_trace(**kwargs)

        def update_current_observation(self, **kwargs: Any) -> None:
            if not tracing_enabled():
                return
            client = get_client()
            model = kwargs.pop("model", None)
            usage = kwargs.pop("usage", None)
            if model is not None or usage is not None:
                usage_details = None
                if usage is not None:
                    usage_details = {
                        "input": usage.get("input", 0),
                        "output": usage.get("output", 0),
                    }
                client.update_current_generation(
                    model=model,
                    usage_details=usage_details,
                    **kwargs,
                )
            else:
                client.update_current_span(**kwargs)

    langfuse_context = _LangfuseContextAdapter()

except Exception:  # pragma: no cover
    observe = _dummy_observe
    langfuse_context = _DummyContext()
