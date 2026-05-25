"""Async orchestration: 5 parallel language agents + 1 synthesis agent."""
from __future__ import annotations
import asyncio
import time
from typing import Any

from ..config import settings
from ..llm_client import get_client
from .prompts import LANG_AGENTS, SYNTHESIZER_SYSTEM, build_user_prompt, build_synthesis_prompt


async def _run_agent(
    system: str,
    user: str,
    max_tokens: int,
    label: str,
) -> dict[str, Any]:
    """Single agent call. Returns content + token + timing."""
    client = get_client()
    started = time.monotonic()
    completion = await client.chat.completions.create(
        model=settings.mimo_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    elapsed = time.monotonic() - started
    msg = completion.choices[0].message.content or ""
    usage = completion.usage
    return {
        "label": label,
        "content": msg,
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
        "elapsed_seconds": round(elapsed, 2),
        "model": settings.mimo_model,
    }


async def run_pipeline(spec_text: str, spec_meta: dict) -> dict[str, Any]:
    """Fan out 5 language agents in parallel, then run synthesis sequentially."""
    pipeline_started = time.monotonic()

    # Stage 1: parallel fan-out
    tasks = [
        _run_agent(
            system=cfg["system"],
            user=build_user_prompt(spec_text, lang),
            max_tokens=settings.per_lang_max_tokens,
            label=cfg["label"],
        )
        for lang, cfg in LANG_AGENTS.items()
    ]
    lang_results = await asyncio.gather(*tasks)
    per_lang = dict(zip(LANG_AGENTS.keys(), lang_results))

    # Stage 2: synthesis
    synth_input = build_synthesis_prompt(
        {lang: r["content"] for lang, r in per_lang.items()},
        spec_meta,
    )
    synth_result = await _run_agent(
        system=SYNTHESIZER_SYSTEM,
        user=synth_input,
        max_tokens=settings.synthesis_max_tokens,
        label="Synthesizer",
    )

    pipeline_elapsed = time.monotonic() - pipeline_started

    total_tokens = sum(r["total_tokens"] for r in lang_results) + synth_result["total_tokens"]
    return {
        "spec_meta": spec_meta,
        "agents": {
            lang: {
                "label": r["label"],
                "content": r["content"],
                "prompt_tokens": r["prompt_tokens"],
                "completion_tokens": r["completion_tokens"],
                "total_tokens": r["total_tokens"],
                "elapsed_seconds": r["elapsed_seconds"],
            }
            for lang, r in per_lang.items()
        },
        "synthesis": {
            "content": synth_result["content"],
            "prompt_tokens": synth_result["prompt_tokens"],
            "completion_tokens": synth_result["completion_tokens"],
            "total_tokens": synth_result["total_tokens"],
            "elapsed_seconds": synth_result["elapsed_seconds"],
        },
        "summary": {
            "total_tokens": total_tokens,
            "wall_clock_seconds": round(pipeline_elapsed, 2),
            "agent_count": len(LANG_AGENTS) + 1,
            "model": settings.mimo_model,
        },
    }
