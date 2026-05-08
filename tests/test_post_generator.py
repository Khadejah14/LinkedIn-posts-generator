"""Tests for post_generator feature."""

import pytest
from unittest.mock import patch, MagicMock

from features.post_generator import generate_posts, add_posts_to_data, add_drafts


SAMPLE_DATA = {
    "my_posts": ["Post one", "Post two", "Post three"],
    "drafts": ["My draft idea"],
    "content_links": [],
}


@patch("features.post_generator.LLM")
@patch("features.post_generator.load_data", return_value=SAMPLE_DATA)
def test_generate_posts_returns_cleaned_text(mock_load, mock_llm_cls):
    mock_llm = MagicMock()
    mock_llm.chat_text.return_value = "Hello — world;; test..."
    mock_llm_cls.return_value = mock_llm

    result = generate_posts(num_posts=1)

    assert isinstance(result, str)
    assert len(result) > 0
    mock_llm.chat_text.assert_called_once()


@patch("features.post_generator.load_data", return_value={"my_posts": [], "drafts": ["d"]})
def test_generate_posts_raises_on_no_posts(mock_load):
    with pytest.raises(ValueError, match="No posts"):
        generate_posts(num_posts=1)


@patch("features.post_generator.load_data", return_value={"my_posts": ["p1", "p2", "p3"], "drafts": []})
def test_generate_posts_raises_on_no_drafts(mock_load):
    with pytest.raises(ValueError, match="No drafts"):
        generate_posts(num_posts=1)


@patch("features.post_generator.save_data")
@patch("features.post_generator.load_data", return_value={"my_posts": ["old"], "drafts": []})
def test_add_posts_to_data_skips_duplicates(mock_load, mock_save):
    add_posts_to_data("old\n#\nnew post")

    saved = mock_save.call_args[0][0]
    assert "old" in saved["my_posts"]
    assert "new post" in saved["my_posts"]
    assert saved["my_posts"].count("old") == 1


@patch("features.post_generator.save_data")
@patch("features.post_generator.load_data", return_value={"my_posts": [], "drafts": ["existing"]})
def test_add_drafts_appends(mock_load, mock_save):
    add_drafts("new draft")

    saved = mock_save.call_args[0][0]
    assert "existing" in saved["drafts"]
    assert "new draft" in saved["drafts"]
