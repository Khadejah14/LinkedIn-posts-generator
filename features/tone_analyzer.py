"""Tone Analyzer feature - extracts voice fingerprint from past posts."""

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path

from llm import LLM
from config import TONE_EXTRACTION_PROMPT, TONE_GENERATION_PROMPT


CACHE_DIR = Path(".tone_cache")
CACHE_TTL = 86400


@dataclass
class ToneProfile:
    vulnerability: float
    humor: float
    formality: float
    story_ratio: float
    hook_style: str
    signature_phrases: list[str]
    emotional_palette: list[str]
    common_topics: list[str]
    voice_signature: str
    tone_summary: str

    def to_dict(self) -> dict:
        return {
            "vulnerability": self.vulnerability,
            "humor": self.humor,
            "formality": self.formality,
            "story_ratio": self.story_ratio,
            "hook_style": self.hook_style,
            "signature_phrases": self.signature_phrases,
            "emotional_palette": self.emotional_palette,
            "common_topics": self.common_topics,
            "voice_signature": self.voice_signature,
            "tone_summary": self.tone_summary,
        }

    @staticmethod
    def from_dict(data: dict) -> "ToneProfile":
        return ToneProfile(
            vulnerability=data.get("vulnerability", 0.0),
            humor=data.get("humor", 0.0),
            formality=data.get("formality", 0.0),
            story_ratio=data.get("story_ratio", 0.0),
            hook_style=data.get("hook_style", ""),
            signature_phrases=data.get("signature_phrases", []),
            emotional_palette=data.get("emotional_palette", []),
            common_topics=data.get("common_topics", []),
            voice_signature=data.get("voice_signature", ""),
            tone_summary=data.get("tone_summary", ""),
        )


def _load_cache(key: str) -> ToneProfile | None:
    import os
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file) as f:
            data = json.load(f)
        if time.time() - data.get("_timestamp", 0) < CACHE_TTL:
            return ToneProfile.from_dict(data.get("profile", {}))
    except:
        pass
    return None


def _save_cache(key: str, profile: ToneProfile) -> None:
    import os
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_DIR / f"{key}.json", "w") as f:
        json.dump({"_timestamp": time.time(), "profile": profile.to_dict()}, f)


def extract_profile(posts: list[str]) -> ToneProfile:
    """Extract voice fingerprint from 3-10 posts."""
    if len(posts) < 3 or len(posts) > 10:
        raise ValueError("Provide between 3 and 10 posts")

    cache_key = hashlib.sha256("|".join(posts).encode()).hexdigest()[:32]
    cached = _load_cache(cache_key)
    if cached:
        return cached

    posts_text = "\n---\n".join([f"Post {i+1}: {p}" for i, p in enumerate(posts)])
    prompt = TONE_EXTRACTION_PROMPT.format(num_posts=len(posts), posts_text=posts_text)

    llm = LLM()
    data = llm.chat(prompt, json_mode=True)
    profile = ToneProfile.from_dict(data)
    _save_cache(cache_key, profile)
    return profile


def generate_with_profile(draft: str, profile: ToneProfile) -> str:
    """Generate post matching a voice profile."""
    prompt = TONE_GENERATION_PROMPT.format(
        vulnerability=profile.vulnerability,
        humor=profile.humor,
        formality=profile.formality,
        story_ratio=profile.story_ratio,
        hook_style=profile.hook_style,
        signature_phrases=", ".join(profile.signature_phrases),
        emotional_palette=", ".join(profile.emotional_palette),
        common_topics=", ".join(profile.common_topics),
        voice_signature=profile.voice_signature,
        tone_summary=profile.tone_summary,
        draft=draft,
    )
    llm = LLM()
    data = llm.chat(prompt, json_mode=True)
    return data.get("post", "")


def compare_drafts(original: str, rewritten: str) -> dict:
    """Compare original vs rewritten drafts."""
    prompt = f"""Compare these two versions of a LinkedIn post.

ORIGINAL:
{original}

REWRITTEN:
{rewritten}

Respond ONLY with valid JSON:
{{
    "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
    "changes": ["<change 1>", "<change 2>", "<change 3>"],
    "readability_improvement": <percentage 0-100>
}}"""
    llm = LLM()
    return llm.chat(prompt, json_mode=True)