"""Example API usage with services layer.

This shows how the services would be called from an API endpoint
(FastAPI, Flask, Streamlit, etc.)
"""

from services.post_service import optimize_post, batch_optimize
from services.analysis_service import analyze_voice, get_available_creators, compare_with_multiple_creators


# Example 1: Optimize a single post
def example_optimize_post():
    draft = "I just landed my dream job at a tech company"
    past_posts = [
        "I never thought I'd switch careers at 30, but here I am...",
        "The best advice I ever got was to just start before you're ready...",
        "Failure taught me more than success ever did...",
    ]
    
    result = optimize_post(
        draft=draft,
        past_posts=past_posts,
        score_hook_flag=True,
    )
    
    print("=== Optimized Post ===")
    print(result["post"])
    if "hook_score" in result:
        print(f"Hook Score: {result['hook_score'].overall}/10")


# Example 2: Batch optimize multiple drafts
def example_batch_optimize():
    drafts = [
        "Just launched my first SaaS product",
        "Why I quit my job to travel the world",
        "3 lessons from my first year in tech",
    ]
    past_posts = [
        "I never thought I'd switch careers at 30...",
        "The best advice I ever got was to just start...",
        "Failure taught me more than success ever did...",
    ]
    
    results = batch_optimize(drafts, past_posts, score_hooks=True)
    
    for i, result in enumerate(results, 1):
        print(f"\n=== Draft {i} ===")
        print(result["post"][:100] + "...")


# Example 3: Analyze voice and compare with creators
def example_analyze_voice():
    past_posts = [
        "I never thought I'd switch careers at 30, but here I am...",
        "The best advice I ever got was to just start before you're ready...",
        "Failure taught me more than success ever did...",
        "Here's what 5 years of coding taught me about patience...",
        "I used to think hard work was enough. I was wrong...",
    ]
    
    # Analyze with one creator comparison
    result = analyze_voice(past_posts, creator_name="Justin Welsh")
    
    print("=== Tone Profile ===")
    profile = result["tone_profile"]
    print(f"Vulnerability: {profile['vulnerability']}")
    print(f"Humor: {profile['humor']}")
    print(f"Hook Style: {profile['hook_style']}")
    
    if "style_comparison" in result:
        comp = result["style_comparison"]
        print(f"\n=== Comparison with {comp['creator_name']} ===")
        print(f"Gaps: {comp['gaps'][:2]}")
        print(f"Actions: {comp['actions'][:2]}")


# Example 4: Compare with multiple creators
def example_multi_creator_comparison():
    past_posts = [
        "I never thought I'd switch careers at 30...",
        "The best advice I ever got was to just start...",
        "Failure taught me more than success ever did...",
    ]
    
    result = compare_with_multiple_creators(
        past_posts,
        creator_names=["Sahil Bloom", "Nicolas Cole"]
    )
    
    print("=== Multi-Creator Comparison ===")
    print(f"Tone Profile: {result['tone_profile']['hook_style']}")
    for comp in result["comparisons"]:
        print(f"\nvs {comp['creator_name']}: {comp['gaps'][:1]}")


# Example 5: FastAPI endpoint example (commented)
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class OptimizeRequest(BaseModel):
    draft: str
    past_posts: list[str] = None
    score_hook: bool = False

class AnalyzeRequest(BaseModel):
    past_posts: list[str]
    creator_name: str = None

@app.post("/api/optimize")
async def optimize_endpoint(req: OptimizeRequest):
    try:
        result = optimize_post(req.draft, req.past_posts, req.score_hook)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analyze")
async def analyze_endpoint(req: AnalyzeRequest):
    try:
        result = analyze_voice(req.past_posts, req.creator_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/creators")
async def get_creators():
    return {"creators": get_available_creators()}
"""


if __name__ == "__main__":
    print("=== Example 1: Optimize Post ===")
    example_optimize_post()
    
    print("\n\n=== Example 3: Analyze Voice ===")
    example_analyze_voice()
    
    print("\n\nAvailable creators:", get_available_creators())
