import json
import os
import re
from pathlib import Path
from typing import Any

from config import DATA_FILE


def load_data() -> dict[str, Any]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"my_posts": [], "drafts": [], "content_links": []}


def save_data(data: dict[str, Any]) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def clean_text(text: str) -> str:
    text = re.sub(r"[-–—;]", "", text)
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


def validate_posts(posts: list[str], min_count: int = 1, max_count: int = 10) -> bool:
    return min_count <= len(posts) <= max_count and all(p.strip() for p in posts)