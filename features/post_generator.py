"""Post Generator feature - transforms drafts into polished LinkedIn posts."""

from llm import LLM
from config import POST_GENERATION_PROMPT
from utils import load_data, save_data, clean_text


def generate_posts(num_posts: int, content_texts: list[str] = None) -> str:
    """Generate polished LinkedIn posts from drafts."""
    data = load_data()
    my_posts = data.get("my_posts", [])
    drafts = data.get("drafts", [])

    if not my_posts:
        raise ValueError("No posts provided. Add your LinkedIn posts first.")
    if not drafts:
        raise ValueError("No drafts provided. Add drafts first.")

    combined_content = "\n".join(content_texts) if content_texts else "No content links provided."

    prompt = POST_GENERATION_PROMPT.format(
        my_posts=my_posts,
        drafts=drafts,
        num_posts=num_posts,
    )

    llm = LLM()
    response = llm.chat_text(prompt, max_tokens=2000)
    return clean_text(response)


def add_posts_to_data(text: str) -> None:
    """Add generated posts to data.json."""
    data = load_data()
    existing = set(data.get("my_posts", []))
    new_posts = [p.strip() for p in text.split("#") if p.strip() and p.strip() not in existing]
    data["my_posts"] = data.get("my_posts", []) + new_posts
    save_data(data)


def add_drafts(text: str) -> None:
    """Add drafts to data.json."""
    data = load_data()
    drafts = data.get("drafts", [])
    new_drafts = [d.strip() for d in text.split("#") if d.strip()]
    data["drafts"] = drafts + new_drafts
    save_data(data)