"""Text and display formatting utilities."""

import re


def clean_text(text: str) -> str:
    text = re.sub(r"[-\u2013\u2014;]", "", text)
    text = re.sub(r"\.{2,}", ".", text)
    return text.strip()


def get_score_color(score: int) -> str:
    if score >= 7:
        return "green"
    elif score >= 4:
        return "yellow"
    return "red"


def render_score_badge(label: str, score: int) -> str:
    color = get_score_color(score)
    return f"**{label}:** :{color}[{score}/10]"


def render_progress(label: str, value: float, max_val: float = 1.0) -> float:
    return value / max_val
