"""AI analyzer for LinkedIn post hooks, topics, tone, and viral patterns."""

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import os


@dataclass
class PostAnalysis:
    hook_type: str
    topic: str
    tone: str
    emotional_appeal: str
    content_format: str
    viral_patterns: list[str]
    cta_type: str
    structure: str
    word_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook_type": self.hook_type,
            "topic": self.topic,
            "tone": self.tone,
            "emotional_appeal": self.emotional_appeal,
            "content_format": self.content_format,
            "viral_patterns": self.viral_patterns,
            "cta_type": self.cta_type,
            "structure": self.structure,
            "word_count": self.word_count,
        }


class PostAnalyzer:
    HOOK_TYPES = [
        "Contrarian Claim",
        "Story Hook",
        "Question",
        "Number List",
        "Provocation",
        "Vulnerability",
        "Result Hook",
        "Failure Story",
        "Instruction",
        "Comparison",
    ]

    TOPICS = [
        "Career",
        "Leadership",
        "Productivity",
        "Entrepreneurship",
        "Hiring",
        "Startups",
        "Failure",
        "Personal Growth",
        "Future of Work",
        "Remote Work",
        "Networking",
        "Mental Health",
        "Work-Life Balance",
        "Management",
        "Sales",
        "Marketing",
        "Fundraising",
        "Networking",
        "Industry Insights",
        "Tips & Tricks",
    ]

    TONES = [
        "Professional",
        "Casual",
        "Bold",
        "Vulnerable",
        "Inspirational",
        "Educational",
        "Humorous",
        "Honest",
        "Raw",
        "Thoughtful",
    ]

    ANALYSIS_PROMPT = """Analyze this LinkedIn post and identify its key elements. Return valid JSON only (no markdown).

POST CONTENT:
{content}

Respond with this exact JSON structure:
{{
    "hook_type": "<one of: Contrarian Claim, Story Hook, Question, Number List, Provocation, Vulnerability, Result Hook, Failure Story, Instruction, Comparison>",
    "topic": "<main topic from: Career, Leadership, Productivity, Entrepreneurship, Hiring, Startups, Failure, Personal Growth, Future of Work, Remote Work, Networking, Mental Health, Work-Life Balance, Management, Sales, Marketing, Fundraising, Industry Insights, Tips & Tricks>",
    "tone": "<tone from: Professional, Casual, Bold, Vulnerable, Inspirational, Educational, Humorous, Honest, Raw, Thoughtful>",
    "emotional_appeal": "<primary emotion from: Curiosity, Excitement, Empathy, Pride, Inspiration, Fear, Nostalgia, Achievement>",
    "content_format": "<format from: Story, List, How-To, Opinion, Question, Announcement, Case Study, Thread>",
    "viral_patterns": ["<list of patterns like: Personal Story, Controversial Take, Numbered List, Before/After, Common Mistake>"],
    "cta_type": "<call-to-action type from: None, Question, Comment Below, Share, Save, Follow, Link>",
    "structure": "<structure from: Hook-Body-CTA, Problem-Solution, Story-Insight, List-Heavy, Single Point>",
    "word_count": <integer>
}}"""

    TOPIC_ANALYSIS_PROMPT = """Analyze these LinkedIn posts and extract the main topics and trends. 
For each post, identify: hook_type, topic, tone.

POSTS:
{posts}

Return a JSON array with one object per post:
[
    {{"post": "<first 100 chars>", "hook_type": "...", "topic": "...", "tone": "..."}},
    ...
]"""

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.cache = {}

    def _call_api(self, prompt: str, cache_key: str = None, max_retries: int = 3) -> dict[str, Any]:
        if cache_key and cache_key in self.cache:
            return self.cache[cache_key]

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000,
                )
                content = response.choices[0].message.content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                data = json.loads(content)
                
                if cache_key:
                    self.cache[cache_key] = data
                return data
            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise

    def analyze_post(self, content: str) -> PostAnalysis:
        import hashlib
        cache_key = f"analyze_{hashlib.sha256(content.encode()).hexdigest()[:32]}"
        prompt = self.ANALYSIS_PROMPT.format(content=content[:2000])
        
        try:
            data = self._call_api(prompt, cache_key)
            return PostAnalysis(
                hook_type=data.get("hook_type", "Unknown"),
                topic=data.get("topic", "General"),
                tone=data.get("tone", "Professional"),
                emotional_appeal=data.get("emotional_appeal", "Neutral"),
                content_format=data.get("content_format", "Story"),
                viral_patterns=data.get("viral_patterns", []),
                cta_type=data.get("cta_type", "None"),
                structure=data.get("structure", "Hook-Body-CTA"),
                word_count=data.get("word_count", 0),
            )
        except Exception as e:
            return self._fallback_analyze(content)

    def _fallback_analyze(self, content: str) -> PostAnalysis:
        content_lower = content.lower()
        word_count = len(content.split())
        
        hook_type = "Story Hook"
        topic = "Career"
        tone = "Professional"
        
        if any(w in content_lower for w in ["mistake", "failure", "lost", "wrong"]):
            hook_type = "Failure Story"
            topic = "Failure"
        elif any(w in content_lower for w in ["turn down", "rejected", "no to"]):
            hook_type = "Contrarian Claim"
            topic = "Career"
        elif any(w in content_lower for w in ["?", "why", "how"]):
            hook_type = "Question"
        elif any(w in content_lower for w in ["tip", "hack", "way", "strategy"]):
            hook_type = "Number List"
            topic = "Productivity"
        
        if any(w in content_lower for w in ["vulnerable", "felt", "emotion", "struggle"]):
            tone = "Vulnerable"
        elif any(w in content_lower for w in ["bold", "truth", "real"]):
            tone = "Bold"
        elif any(w in content_lower for w in ["funny", "lol", "haha"]):
            tone = "Humorous"
        
        emotional_appeal = "Curiosity"
        if "inspire" in content_lower:
            emotional_appeal = "Inspiration"
        elif "fear" in content_lower:
            emotional_appeal = "Fear"
        
        return PostAnalysis(
            hook_type=hook_type,
            topic=topic,
            tone=tone,
            emotional_appeal=emotional_appeal,
            content_format="Story",
            viral_patterns=["Personal Story"],
            cta_type="Comment Below" if "?" in content else "Share",
            structure="Hook-Body-CTA",
            word_count=word_count,
        )

    def analyze_posts(self, posts: list[dict[str, Any]]) -> list[PostAnalysis]:
        results = []
        for post in posts:
            content = post.get("content", post.get("hook", ""))
            if content:
                results.append(self.analyze_post(content))
        return results

    def get_topic_trends(self, posts: list[dict[str, Any]]) -> dict[str, int]:
        trends: dict[str, int] = {}
        for post in posts:
            content = post.get("content", "")
            analysis = self.analyze_post(content)
            trends[analysis.topic] = trends.get(analysis.topic, 0) + 1
        return trends

    def get_hook_type_trends(self, posts: list[dict[str, Any]]) -> dict[str, int]:
        trends: dict[str, int] = {}
        for post in posts:
            content = post.get("content", "")
            analysis = self.analyze_post(content)
            trends[analysis.hook_type] = trends.get(analysis.hook_type, 0) + 1
        return trends

    def get_tone_trends(self, posts: list[dict[str, Any]]) -> dict[str, int]:
        trends: dict[str, int] = {}
        for post in posts:
            content = post.get("content", "")
            analysis = self.analyze_post(content)
            trends[analysis.tone] = trends.get(analysis.tone, 0) + 1
        return trends

    def get_topics_by_competitor(self, posts: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        competitor_topics: dict[str, dict[str, int]] = {}
        
        for post in posts:
            competitor = post.get("competitor_name", "Unknown")
            content = post.get("content", "")
            analysis = self.analyze_post(content)
            
            if competitor not in competitor_topics:
                competitor_topics[competitor] = {}
            competitor_topics[competitor][analysis.topic] = \
                competitor_topics[competitor].get(analysis.topic, 0) + 1
        
        return competitor_topics


class HookGenerator:
    GENERATION_PROMPT = """You are a LinkedIn content expert. Generate variations of this hook in different styles.

ORIGINAL HOOK: "{hook}"

Generate 3 variations:
1. Different angle but same topic
2. Different hook type (e.g., if original is a question, make it a bold claim)
3. More controversial take

Respond with JSON:
{{
    "variations": [
        {{"text": "<variation 1>", "angle": "<angle used>", "hook_type": "<hook type>"}},
        {{"text": "<variation 2>", "angle": "<angle used>", "hook_type": "<hook type>"}},
        {{"text": "<variation 3>", "angle": "<angle used>", "hook_type": "<hook type>"}}
    ]
}}"""

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def generate_variations(self, hook: str, tone: str = "Bold", user_context: str = "") -> list[dict[str, str]]:
        tone_instruction = f"\nTarget tone: {tone}"
        if user_context:
            tone_instruction += f"\nYour content style: {user_context}"
        
        prompt = self.GENERATION_PROMPT.format(hook=hook) + tone_instruction
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            data = json.loads(content)
            return data.get("variations", [])
        except Exception as e:
            return [{"text": f"{hook} (Variation generation failed)", "angle": "Error", "hook_type": "Unknown"}]

    def adapt_to_voice(self, original_hook: str, user_hooks: list[str]) -> str:
        user_hooks_text = "\n".join([f"- {h}" for h in user_hooks[:5]])
        
        prompt = f"""Adapt this competitor hook to match my writing style:

My hooks:
{user_hooks_text}

Competitor hook to adapt: {original_hook}

Keep the core message but write it in MY style - same tone, similar phrasing patterns, my level of boldness.
Return just the adapted hook, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return original_hook