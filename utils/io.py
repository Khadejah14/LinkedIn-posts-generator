"""File I/O utilities for data persistence."""

import json
import os
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
