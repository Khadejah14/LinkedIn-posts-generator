"""Hook Scorer feature - scores hooks and generates variations."""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llm import LLM
from config import HOOK_SCORING_PROMPT, HOOK_VARIATION_PROMPT
from utils import get_score_color


CACHE_DIR = Path(".hook_cache")
CACHE_TTL = 3600


@dataclass
class HookScore:
    overall: int
    scroll_stopping: int
    curiosity: int
    emotion: int
    specificity: int
    brevity: int
    reasoning: str
    improvements: list[str]


def _load_cache(key: str) -> dict | None:
    import os
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file) as f:
            data = json.load(f)
        if time.time() - data.get("_timestamp", 0) < CACHE_TTL:
            return data.get("score")
    except:
        pass
    return None


def _save_cache(key: str, score: dict) -> None:
    import os
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_DIR / f"{key}.json", "w") as f:
        json.dump({"_timestamp": time.time(), "score": score}, f)


def _parse_score(data: dict) -> HookScore:
    criteria = data.get("criteria", data)
    return HookScore(
        overall=data.get("overall", 0),
        scroll_stopping=criteria.get("scroll_stopping", 0),
        curiosity=criteria.get("curiosity", 0),
        emotion=criteria.get("emotion", 0),
        specificity=criteria.get("specificity", 0),
        brevity=criteria.get("brevity", 0),
        reasoning=data.get("reasoning", ""),
        improvements=data.get("improvements", []),
    )


def score_hook(hook: str) -> HookScore:
    """Score a hook on 5 criteria."""
    cache_key = hashlib.sha256(hook.encode()).hexdigest()[:32]
    cached = _load_cache(f"score_{cache_key}")
    if cached:
        return _parse_score(cached)

    llm = LLM()
    prompt = HOOK_SCORING_PROMPT.format(hook=hook)
    data = llm.chat(prompt, json_mode=True)
    _save_cache(f"score_{cache_key}", data)
    return _parse_score(data)


def generate_variations(hook: str) -> list[dict[str, str]]:
    """Generate 3 hook variations with different angles."""
    cache_key = hashlib.sha256(hook.encode()).hexdigest()[:32]
    cached = _load_cache(f"var_{cache_key}")
    if cached:
        return cached.get("variations", [])

    llm = LLM()
    prompt = HOOK_VARIATION_PROMPT.format(hook=hook)
    data = llm.chat(prompt, json_mode=True)
    _save_cache(f"var_{cache_key}", data)
    return data.get("variations", [])


def score_variations(variations: list[str]) -> list[HookScore]:
    """Score multiple variations."""
    return [score_hook(v) for v in variations]