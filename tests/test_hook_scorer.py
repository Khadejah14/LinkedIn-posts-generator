"""Tests for hook_scorer feature."""

import pytest
from unittest.mock import patch, MagicMock

from features.hook_scorer import HookScore, _parse_score, score_hook, generate_variations


SAMPLE_LLM_RESPONSE = {
    "overall": 8,
    "scroll_stopping": 9,
    "curiosity": 7,
    "emotion": 8,
    "specificity": 6,
    "brevity": 9,
    "reasoning": "Strong hook with good emotional pull.",
    "improvements": ["Add a number", "Be more specific"],
}


def test_parse_score_returns_hook_score():
    score = _parse_score(SAMPLE_LLM_RESPONSE)

    assert isinstance(score, HookScore)
    assert score.overall == 8
    assert score.scroll_stopping == 9
    assert score.curiosity == 7
    assert len(score.improvements) == 2


def test_parse_score_handles_nested_criteria():
    nested = {
        "overall": 5,
        "criteria": {
            "scroll_stopping": 4,
            "curiosity": 5,
            "emotion": 6,
            "specificity": 3,
            "brevity": 7,
        },
        "reasoning": "Decent",
        "improvements": [],
    }
    score = _parse_score(nested)

    assert score.scroll_stopping == 4
    assert score.brevity == 7


def test_parse_score_defaults_to_zero():
    score = _parse_score({})

    assert score.overall == 0
    assert score.scroll_stopping == 0
    assert score.improvements == []


@patch("features.hook_scorer._load_cache", return_value=SAMPLE_LLM_RESPONSE)
def test_score_hook_returns_cached(mock_cache):
    score = score_hook("test hook")

    assert isinstance(score, HookScore)
    assert score.overall == 8


@patch("features.hook_scorer._load_cache", return_value=None)
@patch("features.hook_scorer._save_cache")
@patch("features.hook_scorer.LLM")
def test_score_hook_calls_llm_on_miss(mock_llm_cls, mock_save, mock_cache):
    mock_llm = MagicMock()
    mock_llm.chat.return_value = SAMPLE_LLM_RESPONSE
    mock_llm_cls.return_value = mock_llm

    score = score_hook("new hook")

    assert score.overall == 8
    mock_llm.chat.assert_called_once()
    mock_save.assert_called_once()


@patch("features.hook_scorer._load_cache")
def test_generate_variations_returns_list(mock_cache):
    mock_cache.return_value = {"variations": [{"text": "v1", "angle": "curiosity"}]}

    result = generate_variations("test hook")

    assert isinstance(result, list)
    assert result[0]["text"] == "v1"
