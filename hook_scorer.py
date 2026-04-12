"""Hook Scoring module for LinkedIn posts using gpt-4o-mini."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


CACHE_DIR = Path(__file__).parent / ".hook_cache"
CACHE_TTL = 3600
MAX_RETRIES = 3
RETRY_DELAY = 1.0


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "criteria": {
                "scroll_stopping": self.scroll_stopping,
                "curiosity": self.curiosity,
                "emotion": self.emotion,
                "specificity": self.specificity,
                "brevity": self.brevity,
            },
            "reasoning": self.reasoning,
            "improvements": self.improvements,
        }


class Cache:
    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self._memory_cache: dict[str, tuple[float, HookScore]] = {}

    def _get_cache_path(self, key: str) -> Path:
        hash_key = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{hash_key}.json"

    def get(self, key: str) -> HookScore | None:
        if key in self._memory_cache:
            timestamp, score = self._memory_cache[key]
            if time.time() - timestamp < CACHE_TTL:
                return score
            del self._memory_cache[key]

        path = self._get_cache_path(key)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                timestamp = data.get("_timestamp", 0)
                if time.time() - timestamp < CACHE_TTL:
                    score = self._dict_to_score(data["score"])
                    self._memory_cache[key] = (timestamp, score)
                    return score
            except (json.JSONDecodeError, IOError, KeyError):
                pass
        return None

    def set(self, key: str, score: HookScore) -> None:
        timestamp = time.time()
        self._memory_cache[key] = (timestamp, score)
        path = self._get_cache_path(key)
        data = {"_timestamp": timestamp, "score": score.to_dict()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def _dict_to_score(data: dict[str, Any]) -> HookScore:
        criteria = data.get("criteria", {})
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


class HookScorer:
    SCORING_PROMPT = """You are an expert LinkedIn content strategist specializing in hook optimization.

Rate the following LinkedIn post hook on a scale of 1-10 for each criterion:

1. SCROLL_STOPPING (1-10): Does it immediately grab attention? Would someone stop scrolling?
2. CURIOSITY (1-10): Does it create curiosity gaps? Make readers want to learn more?
3. EMOTION (1-10): Does it evoke emotions (surprise, excitement, empathy, etc.)?
4. SPECIFICITY (1-10): Is it concrete and specific rather than vague/generic?
5. BREVITY (1-10): Is it concise? Can it be read in under 3 seconds?

HOOK TO EVALUATE:
"{hook}"

Respond ONLY with valid JSON in this exact format, no markdown, no code blocks:
{{
    "overall": <1-10 integer>,
    "scroll_stopping": <1-10 integer>,
    "curiosity": <1-10 integer>,
    "emotion": <1-10 integer>,
    "specificity": <1-10 integer>,
    "brevity": <1-10 integer>,
    "reasoning": "<2-3 sentence explanation of the overall score>",
    "improvements": ["<specific improvement 1>", "<specific improvement 2>", "<specific improvement 3>"]
}}"""

    VARIATION_PROMPT = """You are a LinkedIn content expert. Generate 3 different variations of the following hook, each with a distinct angle/strategy.

HOOK: "{hook}"

Create 3 variations that are:
- Scroll-stopping and attention-grabbing
- Concise (under 15 words each)
- Each with a different emotional angle or approach

Respond ONLY with valid JSON, no markdown:
{{
    "variations": [
        {{"text": "<variation 1>", "angle": "<emotional angle used>"}},
        {{"text": "<variation 2>", "angle": "<emotional angle used>"}},
        {{"text": "<variation 3>", "angle": "<emotional angle used>"}}
    ]
}}"""

    def __init__(self, api_key: str | None = None, cache_dir: Path = CACHE_DIR) -> None:
        self.client = OpenAI(api_key=api_key)
        self.cache = Cache(cache_dir)

    def _make_request(self, prompt: str, cache_key: str | None = None) -> dict[str, Any]:
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached:
                return cached.to_dict()

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500,
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                data = json.loads(content)

                if cache_key:
                    score = self._dict_to_score(data)
                    self.cache.set(cache_key, score)

                return data
            except json.JSONDecodeError as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                continue

        raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: {last_error}")

    def _dict_to_score(self, data: dict[str, Any]) -> HookScore:
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

    def score_hook(self, hook: str) -> HookScore:
        cache_key = f"score_{hashlib.sha256(hook.encode()).hexdigest()[:32]}"
        prompt = self.SCORING_PROMPT.format(hook=hook)
        data = self._make_request(prompt, cache_key)
        return self._dict_to_score(data)

    def generate_variations(self, hook: str) -> list[dict[str, str]]:
        cache_key = f"var_{hashlib.sha256(hook.encode()).hexdigest()[:32]}"
        prompt = self.VARIATION_PROMPT.format(hook=hook)
        data = self._make_request(prompt, cache_key)
        return data.get("variations", [])

    def score_variations(self, variations: list[str]) -> list[HookScore]:
        scores = []
        for var in variations:
            scores.append(self.score_hook(var))
        return scores
