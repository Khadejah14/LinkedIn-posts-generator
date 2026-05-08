"""Tests for tone_analyzer feature."""

import pytest
from unittest.mock import patch, MagicMock

from features.tone_analyzer import ToneProfile, extract_profile, generate_with_profile


SAMPLE_PROFILE_DATA = {
    "vulnerability": 0.7,
    "humor": 0.3,
    "formality": 0.4,
    "story_ratio": 0.6,
    "hook_style": "question",
    "signature_phrases": ["honestly", "I guess"],
    "emotional_palette": ["empathy", "curiosity"],
    "common_topics": ["loneliness", "growth"],
    "voice_signature": "Casual and vulnerable.",
    "tone_summary": "Conversational with personal stories.",
}


def test_tone_profile_from_dict():
    profile = ToneProfile.from_dict(SAMPLE_PROFILE_DATA)

    assert profile.vulnerability == 0.7
    assert profile.humor == 0.3
    assert profile.hook_style == "question"
    assert "honestly" in profile.signature_phrases


def test_tone_profile_to_dict():
    profile = ToneProfile.from_dict(SAMPLE_PROFILE_DATA)
    result = profile.to_dict()

    assert isinstance(result, dict)
    assert result["vulnerability"] == 0.7
    assert result["hook_style"] == "question"
    assert "empathy" in result["emotional_palette"]


def test_tone_profile_from_dict_defaults():
    profile = ToneProfile.from_dict({})

    assert profile.vulnerability == 0.0
    assert profile.humor == 0.0
    assert profile.hook_style == ""
    assert profile.signature_phrases == []


def test_tone_profile_roundtrip():
    original = ToneProfile.from_dict(SAMPLE_PROFILE_DATA)
    reconstructed = ToneProfile.from_dict(original.to_dict())

    assert reconstructed.vulnerability == original.vulnerability
    assert reconstructed.hook_style == original.hook_style
    assert reconstructed.signature_phrases == original.signature_phrases


def test_extract_profile_rejects_too_few():
    with pytest.raises(ValueError, match="between 3 and 10"):
        extract_profile(["post1", "post2"])


def test_extract_profile_rejects_too_many():
    posts = [f"post {i}" for i in range(11)]
    with pytest.raises(ValueError, match="between 3 and 10"):
        extract_profile(posts)


@patch("features.tone_analyzer._load_cache")
def test_extract_profile_returns_cached(mock_cache):
    mock_cache.return_value = ToneProfile.from_dict(SAMPLE_PROFILE_DATA)

    profile = extract_profile(["p1", "p2", "p3"])

    assert isinstance(profile, ToneProfile)
    assert profile.vulnerability == 0.7


@patch("features.tone_analyzer._load_cache", return_value=None)
@patch("features.tone_analyzer._save_cache")
@patch("features.tone_analyzer.LLM")
def test_extract_profile_calls_llm_on_miss(mock_llm_cls, mock_save, mock_cache):
    mock_llm = MagicMock()
    mock_llm.chat.return_value = SAMPLE_PROFILE_DATA
    mock_llm_cls.return_value = mock_llm

    profile = extract_profile(["post a", "post b", "post c"])

    assert profile.hook_style == "question"
    mock_llm.chat.assert_called_once()
    mock_save.assert_called_once()


@patch("features.tone_analyzer.LLM")
def test_generate_with_profile_returns_post(mock_llm_cls):
    mock_llm = MagicMock()
    mock_llm.chat.return_value = {"post": "Generated LinkedIn post"}
    mock_llm_cls.return_value = mock_llm

    profile = ToneProfile.from_dict(SAMPLE_PROFILE_DATA)
    result = generate_with_profile("my draft", profile)

    assert result == "Generated LinkedIn post"
    mock_llm.chat.assert_called_once()
