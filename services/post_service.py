"""Post Service - coordinates post generation workflow."""

from features.tone_analyzer import extract_profile, generate_with_profile, ToneProfile
from features.post_generator import generate_posts, add_drafts
from features.hook_scorer import score_hook, HookScore
from typing import Optional


def optimize_post(
    draft: str,
    past_posts: list[str] = None,
    score_hook_flag: bool = False,
) -> dict:
    """
    Create optimized post from user draft.
    
    Args:
        draft: User's draft content
        past_posts: Optional past posts for tone analysis
        score_hook_flag: Whether to score the hook
        
    Returns:
        Dict with 'post' and optionally 'hook_score'
    """
    profile = None
    if past_posts and len(past_posts) >= 3:
        profile = extract_profile(past_posts)

    if profile:
        post = generate_with_profile(draft, profile)
    else:
        add_drafts(draft)
        post = generate_posts(num_posts=1)

    result = {"post": post}

    if score_hook_flag and post:
        hook = post.split("\n")[0][:200]
        result["hook_score"] = score_hook(hook)

    return result


def batch_optimize(
    drafts: list[str],
    past_posts: list[str] = None,
    score_hooks: bool = False,
) -> list[dict]:
    """Optimize multiple drafts."""
    return [optimize_post(d, past_posts, score_hooks) for d in drafts]
