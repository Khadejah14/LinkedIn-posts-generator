"""Analysis Service - combines tone analysis and style comparison."""

from features.tone_analyzer import extract_profile, ToneProfile
from features.style_comparison import (
    compare_with_creator,
    get_creator_names,
    get_radar_data,
    StyleComparison,
)
from utils.cache import cached, get_cache
from typing import Optional


@cached(ttl=3600)
def analyze_voice(
    past_posts: list[str],
    creator_name: str = None,
) -> dict:
    """
    Analyze user voice and optionally compare with creator style.

    Args:
        past_posts: User's past posts for tone analysis
        creator_name: Optional creator to compare against

    Returns:
        Dict with tone_profile and optional style_comparison
    """
    profile = extract_profile(past_posts)
    profile_dict = profile.to_dict()

    result = {"tone_profile": profile_dict}

    if creator_name:
        comparison = compare_with_creator(profile_dict, creator_name)
        result["style_comparison"] = {
            "creator_name": comparison.creator_name,
            "gaps": comparison.gaps,
            "unique_traits": comparison.unique_traits,
            "missing_traits": comparison.missing_traits,
            "actions": comparison.actions,
            "adoptable_traits": comparison.adoptable_traits,
        }
        result["radar_data"] = get_radar_data(profile_dict, comparison.creator_profile)

    return result


def get_available_creators() -> list[str]:
    """Get list of available creators for style comparison."""
    return get_creator_names()


@cached(ttl=3600)
def compare_with_multiple_creators(
    past_posts: list[str],
    creator_names: list[str] = None,
) -> dict:
    """Compare user voice with multiple creators."""
    profile = extract_profile(past_posts)
    profile_dict = profile.to_dict()

    if not creator_names:
        creator_names = get_available_creators()

    comparisons = []
    for name in creator_names:
        comp = compare_with_creator(profile_dict, name)
        comparisons.append({
            "creator_name": comp.creator_name,
            "gaps": comp.gaps,
            "unique_traits": comp.unique_traits,
            "radar_data": get_radar_data(profile_dict, comp.creator_profile),
        })

    return {
        "tone_profile": profile_dict,
        "comparisons": comparisons,
    }
