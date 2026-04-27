"""Style Comparison feature - compare user voice against top LinkedIn creators."""

from dataclasses import dataclass, field
from typing import Optional
import json

from config import STYLE_COMPARISON_PROMPT
from llm import LLM


CREATOR_PROFILES = {
    "Sahil Bloom": {
        "vulnerability": 0.7,
        "humor": 0.3,
        "formality": 0.4,
        "story_ratio": 0.8,
        "hook_style": "curiosity gap",
        "signature_phrases": ["Here's the thing", "Let me share", "I've been thinking"],
        "emotional_palette": ["curiosity", "inspiration", "wonder", "awe"],
        "common_topics": ["mental models", "wealth", "success", "life lessons"],
        "voice_signature": "Story-driven insights with curiosity hooks and actionable wisdom",
        "tone_summary": "Warm, conversational, story-first",
    },
    "Nicolas Cole": {
        "vulnerability": 0.8,
        "humor": 0.2,
        "formality": 0.3,
        "story_ratio": 0.9,
        "hook_style": "contrarian",
        "signature_phrases": ["The truth is", "Nobody talks about", "I realized"],
        "emotional_palette": ["honesty", "determination", "vulnerability", "grit"],
        "common_topics": ["writing", "discipline", "career", "personal growth"],
        "voice_signature": "Brutally honest personal stories with contrarian angles",
        "tone_summary": "Raw, unfiltered, deeply personal",
    },
    "Justin Welsh": {
        "vulnerability": 0.5,
        "humor": 0.1,
        "formality": 0.6,
        "story_ratio": 0.4,
        "hook_style": "list/practical",
        "signature_phrases": ["Here are", "Simple system", "3 lessons"],
        "emotional_palette": ["calm", "clarity", "focus", "balance"],
        "common_topics": ["productivity", "solopreneur", "systems", "habits"],
        "voice_signature": "Calm, structured, practical advice with minimal fluff",
        "tone_summary": "Composed, systematic, value-dense",
    },
    "Alex Hormozi": {
        "vulnerability": 0.6,
        "humor": 0.4,
        "formality": 0.2,
        "story_ratio": 0.5,
        "hook_style": "bold claim",
        "signature_phrases": ["We found", "The secret", "Most people"],
        "emotional_palette": ["intensity", "confidence", "urgency", "excitement"],
        "common_topics": ["business", "sales", "growth", "acquisition"],
        "voice_signature": "High-energy bold claims backed by specific tactics",
        "tone_summary": "Intense, direct, action-oriented",
    },
    "Lara Acosta": {
        "vulnerability": 0.9,
        "humor": 0.5,
        "formality": 0.3,
        "story_ratio": 0.7,
        "hook_style": "personal revelation",
        "signature_phrases": ["I used to", "My biggest", "When I"],
        "emotional_palette": ["vulnerability", "empathy", "resilience", "growth"],
        "common_topics": ["immigration", "tech", "personal branding", "mindset"],
        "voice_signature": "Deeply vulnerable immigrant journey stories with empowering lessons",
        "tone_summary": "Emotional, authentic, inspiring",
    },
}


@dataclass
class StyleComparison:
    creator_name: str
    user_profile: dict
    creator_profile: dict
    gaps: list[str]
    unique_traits: list[str]
    missing_traits: list[str]
    actions: list[str]
    adoptable_traits: dict[str, float] = field(default_factory=dict)


def get_creator_names() -> list[str]:
    return list(CREATOR_PROFILES.keys())


def get_creator_profile(name: str) -> Optional[dict]:
    return CREATOR_PROFILES.get(name)


def compare_with_creator(user_profile: dict, creator_name: str) -> StyleComparison:
    """Compare user voice profile against a creator."""
    creator_profile = CREATOR_PROFILES.get(creator_name)
    if not creator_profile:
        raise ValueError(f"Creator '{creator_name}' not found")

    llm = LLM()
    prompt = STYLE_COMPARISON_PROMPT.format(
        user_profile=json.dumps(user_profile, indent=2),
        creator_name=creator_name,
        creator_profile=json.dumps(creator_profile, indent=2),
    )

    response = llm.chat(prompt, json_mode=True)

    return StyleComparison(
        creator_name=creator_name,
        user_profile=user_profile,
        creator_profile=creator_profile,
        gaps=response.get("gaps", []),
        unique_traits=response.get("unique_traits", []),
        missing_traits=response.get("missing_traits", []),
        actions=response.get("actions", []),
        adoptable_traits=response.get("adoptable_traits", {}),
    )


def get_radar_data(user_profile: dict, creator_profile: dict) -> dict:
    """Extract radar chart data for visualization."""
    dimensions = ["vulnerability", "humor", "formality", "story_ratio"]

    return {
        "dimensions": dimensions,
        "user_values": [user_profile.get(d, 0.0) for d in dimensions],
        "creator_values": [creator_profile.get(d, 0.0) for d in dimensions],
    }
