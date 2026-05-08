"""Input validation utilities."""


def validate_posts(posts: list[str], min_count: int = 1, max_count: int = 10) -> bool:
    return min_count <= len(posts) <= max_count and all(p.strip() for p in posts)
