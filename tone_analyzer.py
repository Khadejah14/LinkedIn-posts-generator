"""Tone Analyzer for LinkedIn posts - extracts voice fingerprint from past posts."""

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


CACHE_DIR = Path(__file__).parent / ".tone_cache"
CACHE_TTL = 86400
MAX_RETRIES = 3
RETRY_DELAY = 1.0


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

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(data: dict[str, Any]) -> ToneProfile:
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


class ProfileCache:
    def __init__(self, cache_dir: Path = CACHE_DIR) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self._memory_cache: dict[str, tuple[float, ToneProfile]] = {}

    def _get_cache_key(self, posts: list[str]) -> str:
        combined = "|".join(posts)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, posts: list[str]) -> ToneProfile | None:
        key = self._get_cache_key(posts)
        if key in self._memory_cache:
            timestamp, profile = self._memory_cache[key]
            if time.time() - timestamp < CACHE_TTL:
                return profile

        path = self._get_cache_path(key)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                timestamp = data.get("_timestamp", 0)
                if time.time() - timestamp < CACHE_TTL:
                    profile = ToneProfile.from_dict(data["profile"])
                    self._memory_cache[key] = (timestamp, profile)
                    return profile
            except (json.JSONDecodeError, IOError, KeyError):
                pass
        return None

    def set(self, posts: list[str], profile: ToneProfile) -> None:
        key = self._get_cache_key(posts)
        timestamp = time.time()
        self._memory_cache[key] = (timestamp, profile)
        path = self._get_cache_path(key)
        data = {"_timestamp": timestamp, "profile": profile.to_dict()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


class ToneAnalyzer:
    EXTRACTION_PROMPT = """You are a LinkedIn content analyst. Analyze the following {num_posts} LinkedIn posts to extract a voice fingerprint.

For each dimension, provide a score from 0.0 to 1.0:
- VULNERABILITY: How much do they share personal struggles/failures/weaknesses?
- HUMOR: How often do they use jokes, wit, irony, or lighthearted moments?
- FORMALITY: How professional/corporate is the language vs casual/conversational?
- STORY_RATIO: What proportion of content is storytelling vs advice/tips?

Also identify:
- HOOK_STYLE: How do they start posts? (question, bold claim, story intro, contrarian, list, etc.)
- SIGNATURE_PHRASES: 3-5 recurring phrases or patterns that feel "them"
- EMOTIONAL_PALETTE: 5-7 emotions they typically evoke (e.g., inspiration, curiosity, nostalgia, empathy, excitement, etc.)
- COMMON_TOPICS: 5-7 recurring themes or topics
- VOICE_SIGNATURE: 2-3 sentence description of their unique voice
- TONE_SUMMARY: Brief summary of their overall tone

POSTS:
{posts_text}

Respond ONLY with valid JSON, no markdown:
{{
    "vulnerability": <0.0-1.0>,
    "humor": <0.0-1.0>,
    "formality": <0.0-1.0>,
    "story_ratio": <0.0-1.0>,
    "hook_style": "<primary hook style>",
    "signature_phrases": ["<phrase1>", "<phrase2>", "<phrase3>"],
    "emotional_palette": ["<emotion1>", "<emotion2>", "<emotion3>", "<emotion4>", "<emotion5>"],
    "common_topics": ["<topic1>", "<topic2>", "<topic3>", "<topic4>", "<topic5>"],
    "voice_signature": "<2-3 sentence voice description>",
    "tone_summary": "<brief tone summary>"
}}"""

    GENERATION_PROMPT = """You are a LinkedIn content writer. Write a new LinkedIn post that matches the following voice fingerprint:

VOICE FINGERPRINT:
- Vulnerability: {vulnerability}
- Humor: {humor}
- Formality: {formality}
- Story Ratio: {story_ratio}
- Hook Style: {hook_style}
- Signature Phrases: {signature_phrases}
- Emotional Palette: {emotional_palette}
- Common Topics: {common_topics}
- Voice Signature: {voice_signature}
- Tone Summary: {tone_summary}

DRAFT CONTENT:
{draft}

Rewrite the draft into a polished LinkedIn post that:
- Uses the same hook style as their past posts
- Incorporates similar signature phrases naturally
- Matches the vulnerability, humor, formality, and story ratio levels
- Evokes emotions from their palette
- Stays on topic with their common themes
- Has their voice signature tone
- NEVER use dashes (-, –, —)
- NEVER use semicolons (;)
- Keep sentences flowing with commas, avoid excessive periods
- Start with a scroll-stopping hook matching their style

Respond ONLY with valid JSON:
{{"post": "<rewritten post>"}}"""

    def __init__(self, api_key: str | None = None, cache_dir: Path = CACHE_DIR) -> None:
        self.client = OpenAI(api_key=api_key)
        self.cache = ProfileCache(cache_dir)

    def _make_request(self, prompt: str) -> dict[str, Any]:
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000,
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                return json.loads(content)
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

    def extract_profile(self, posts: list[str]) -> ToneProfile:
        if len(posts) < 3 or len(posts) > 10:
            raise ValueError("Provide between 3 and 10 posts")

        cached = self.cache.get(posts)
        if cached:
            return cached

        posts_text = "\n---\n".join([f"Post {i+1}: {p}" for i, p in enumerate(posts)])
        prompt = self.EXTRACTION_PROMPT.format(num_posts=len(posts), posts_text=posts_text)
        data = self._make_request(prompt)
        profile = ToneProfile.from_dict(data)
        self.cache.set(posts, profile)
        return profile

    def generate_with_profile(self, draft: str, profile: ToneProfile) -> str:
        prompt = self.GENERATION_PROMPT.format(
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
        return self._make_request(prompt).get("post", "")

    def compare_drafts(self, original: str, rewritten: str) -> dict[str, Any]:
        comparison_prompt = f"""Compare these two versions of a LinkedIn post. Analyze how the rewrite improved or changed the original.

ORIGINAL:
{original}

REWRITTEN:
{rewritten}

Respond ONLY with valid JSON:
{{
    "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
    "changes": ["<change 1>", "<change 2>", "<change 3>"],
    "hook_comparison": {{"original": "<original hook>", "rewritten": "<rewritten hook>"}},
    "tone_shift": "<how the tone shifted>",
    "readability_improvement": <percentage 0-100>
}}"""

        return self._make_request(comparison_prompt)