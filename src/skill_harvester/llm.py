"""LLM backend abstraction.

设计原则:
- 统一接口: 输入 system + user prompt, 要求 JSON 输出
- 三个后端: mock (开发用) / anthropic / openai
- mock 后端的回答是确定的, 让单元测试和 Phase 0 早期验证能脱离网络跑
"""

from __future__ import annotations

import json
import os
from typing import Any, Protocol


class LLMBackend(Protocol):
    name: str
    def complete_json(self, system: str, user: str) -> dict[str, Any]: ...


# ----------------------------------------------------------------------------
# Mock backend
# ----------------------------------------------------------------------------

class MockLLM:
    """A deterministic stub for development and Phase 0 dry runs.

    它总是返回 task_id='other' + 低置信度, 让 fallback 路径被走到。
    Production 归纳时返回一条最朴素的规则。
    """
    name = "mock"

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        # Crude routing by looking at the system prompt
        if "classify" in system.lower() or "task_id" in system.lower():
            return {
                "task_id": "other",
                "confidence": 0.3,
                "reason": "[mock] classifier did not run, returning fallback",
            }
        if "induce" in system.lower() or "production" in system.lower():
            return {
                "productions": [
                    {
                        "intent": {
                            "goal": "mock_goal",
                            "conditions": ["[mock] condition placeholder"],
                            "business_action": "mock_action",
                            "rationale": "[mock] induced from sample episodes",
                        },
                        "execution": {
                            "tool": "mock_tool",
                            "args": {},
                            "fallback_tool": "browser_use",
                            "fallback_hint": "[mock] fallback",
                        },
                        "utility": 0.5,
                    }
                ]
            }
        return {}


# ----------------------------------------------------------------------------
# Anthropic backend
# ----------------------------------------------------------------------------

class AnthropicLLM:
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-4-6"):
        try:
            import anthropic  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "anthropic backend selected but `anthropic` package not installed. "
                "pip install skill-harvester[anthropic]"
            ) from e
        self.model = model

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system + "\n\nIMPORTANT: respond with a single JSON object, no prose.",
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text"))
        return _extract_json(text)


# ----------------------------------------------------------------------------
# OpenAI backend
# ----------------------------------------------------------------------------

class OpenAILLM:
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini"):
        try:
            import openai  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "openai backend selected but `openai` package not installed. "
                "pip install skill-harvester[openai]"
            ) from e
        self.model = model

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return json.loads(resp.choices[0].message.content or "{}")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _extract_json(text: str) -> dict[str, Any]:
    """Best-effort JSON extraction for backends that don't enforce JSON mode."""
    text = text.strip()
    # strip ```json fences if present
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # last resort: find first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def get_backend() -> LLMBackend:
    """Read $SKILL_HARVESTER_LLM and instantiate the chosen backend."""
    name = os.environ.get("SKILL_HARVESTER_LLM", "mock").lower()
    if name == "mock":
        return MockLLM()
    if name == "anthropic":
        return AnthropicLLM()
    if name == "openai":
        return OpenAILLM()
    raise ValueError(f"Unknown LLM backend: {name}")
