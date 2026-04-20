"""Gap analysis module for identifying topic/angle opportunities."""

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class Gap:
    topic: str
    angle: str
    opportunity_score: float
    description: str
    competitor_examples: list[str]


class GapAnalyzer:
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def analyze_gaps(
        self,
        competitor_analysis: list[dict[str, Any]],
        user_topics: list[str],
        user_hooks: list[str] = None,
    ) -> list[Gap]:
        competitor_topics = self._extract_topics(competitor_analysis)
        competitor_hooks = self._extract_hooks(competitor_analysis)
        
        gaps = []
        
        competitor_topic_set = set(competitor_topics.keys())
        user_topic_set = set(user_topics) if user_topics else set()
        
        missing_topics = competitor_topic_set - user_topic_set
        
        for topic in missing_topics:
            freq = competitor_topics[topic]
            opportunity_score = min(freq / 10.0, 1.0)
            
            topic_angles = self._get_topic_angles(topic, competitor_analysis)
            for angle in topic_angles:
                gaps.append(Gap(
                    topic=topic,
                    angle=angle,
                    opportunity_score=opportunity_score,
                    description=f"Competitors posting about {topic} with {angle}, but you haven't covered this yet.",
                    competitor_examples=self._get_examples(topic, angle, competitor_analysis)
                ))
        
        for topic, count in competitor_topics.items():
            if topic in user_topic_set:
                angles = self._get_topic_angles(topic, competitor_analysis)
                topic_coverage = sum(1 for a in angles if a in (user_hooks or []))
                
                if topic_coverage < len(angles) * 0.5:
                    gaps.append(Gap(
                        topic=topic,
                        angle="Under-explored angle",
                        opportunity_score=0.3 * count / 10,
                        description=f"You've posted about {topic}, but competitors are using angles you haven't tried.",
                        competitor_examples=self._get_examples(topic, None, competitor_analysis)
                    ))
        
        gaps.sort(key=lambda x: x.opportunity_score, reverse=True)
        return gaps[:10]

    def _extract_topics(self, analysis_data: list[dict[str, Any]]) -> dict[str, int]:
        topics: dict[str, int] = {}
        for item in analysis_data:
            topic = item.get("topic", "Unknown")
            if topic:
                topics[topic] = topics.get(topic, 0) + 1
        return topics

    def _extract_hooks(self, analysis_data: list[dict[str, Any]]) -> dict[str, int]:
        hooks: dict[str, int] = {}
        for item in analysis_data:
            hook_type = item.get("hook_type", "Unknown")
            if hook_type:
                hooks[hook_type] = hooks.get(hook_type, 0) + 1
        return hooks

    def _get_topic_angles(self, topic: str, analysis_data: list[dict[str, Any]]) -> list[str]:
        angles = []
        for item in analysis_data:
            if item.get("topic", "").lower() == topic.lower():
                hook_type = item.get("hook_type", "")
                tone = item.get("tone", "")
                if hook_type:
                    angles.append(f"{hook_type} ({tone})")
        return list(set(angles))[:5]

    def _get_examples(
        self,
        topic: str,
        angle: str | None,
        analysis_data: list[dict[str, Any]],
    ) -> list[str]:
        examples = []
        for item in analysis_data[:5]:
            if item.get("topic", "").lower() == topic.lower():
                content = item.get("content", "")[:100]
                if content:
                    examples.append(content)
        return examples[:3]

    def generate_topic_ideas(self, competitor_analysis: list[dict[str, Any]], user_topics: list[str]) -> list[str]:
        combined_prompt = self._build_topic_prompt(competitor_analysis, user_topics)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": combined_prompt}],
                temperature=0.8,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            return [line for line in lines if line and not line.startswith("#")][:10]
        except Exception:
            return self._fallback_topic_ideas(competitor_analysis)

    def _build_topic_prompt(self, competitor_analysis: list[dict[str, Any]], user_topics: list[str]) -> str:
        competitor_data = "\n".join([
            f"- {item.get('topic', 'Unknown')}: {item.get('hook_type', '')} ({item.get('tone', '')})"
            for item in competitor_analysis[:20]
        ])
        
        user_data = "\n".join([f"- {t}" for t in user_topics]) if user_topics else "- (No user topics provided)"
        
        return f"""Based on this gap analysis data, suggest 5-10 topics/angles that are:
1. Popular with competitors but NOT covered by the user
2. Have high viral potential

Competitor data:
{competitor_data}

User topics:
{user_data}

Return a simple bullet list of topic ideas (one per line, no numbers)."""

    def _fallback_topic_ideas(self, competitor_analysis: list[dict[str, Any]]) -> list[str]:
        topic_counts: Counter = Counter()
        for item in competitor_analysis:
            topic = item.get("topic", "Unknown")
            topic_counts[topic] += 1
        
        return [f"Topic: {topic} (Competitors posting {count}+ times)"
                for topic, count in topic_counts.most_common(10)]

    def get_trend_insights(self, competitor_analysis: list[dict[str, Any]]) -> dict[str, Any]:
        hook_types = Counter()
        topics = Counter()
        tones = Counter()
        emotional_appeals = Counter()
        viral_patterns_counter: Counter = Counter()
        
        for item in competitor_analysis:
            hook_type = item.get("hook_type", "Unknown")
            topic = item.get("topic", "General")
            tone = item.get("tone", "Neutral")
            emotion = item.get("emotional_appeal", "Neutral")
            
            if hook_type:
                hook_types[hook_type] += 1
            if topic:
                topics[topic] += 1
            if tone:
                tones[tone] += 1
            if emotion:
                emotional_appeals[emotion] += 1
            
            for pattern in item.get("viral_patterns", []):
                if pattern:
                    viral_patterns_counter[pattern] += 1
        
        return {
            "top_hook_types": hook_types.most_common(5),
            "top_topics": topics.most_common(10),
            "top_tones": tones.most_common(5),
            "top_emotional_appeals": emotional_appeals.most_common(5),
            "viral_patterns": viral_patterns_counter.most_common(5),
            "total_analyzed": len(competitor_analysis),
        }