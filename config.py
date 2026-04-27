import os

DATA_FILE = "data/data.json"
MAX_FILE_SIZE = 25 * 1024 * 1024
DEFAULT_MODEL = "gpt-4o-mini"

FILLER_WORDS = [
    r"\b(um|uh|er|ah|like|you know|basically|actually|seriously|honestly)\b",
    r"\b(i mean|i guess|i think|i know right|i'll be like|i'm just saying)\b",
    r"\b(yeah|no|okay|right|so|well|then|you know)\b",
]

POST_GENERATION_PROMPT = """You are a LinkedIn content assistant. I will provide:

1. My previous LinkedIn posts (this is my style and tone, including hooks):
{my_posts}

2. My raw drafts or ramblings (rewrite these into polished LinkedIn posts):
{drafts}

Rewrite and transform the drafts into {num_posts} polished LinkedIn posts, keeping my style consistent with my past posts.

Rules for generated posts:
- Start with a short, catchy, scroll-stopping hook at the beginning, following the hook style in my posts (think like Gen Z)
- Hooks should be concise, 1 sentence, grab attention immediately
- After the hook, rewrite the draft content into a flowing, engaging post using my style
- NEVER use any dashes (-, –, —)
- NEVER use semicolons (;)
- Use commas instead of many periods, keep sentences flowing naturally
- Avoid bad words like f*ck
- Separate each post with a single "#" on a new line
"""

STRUCTURE_DRAFT_PROMPT = """Analyze the following transcript and structure it into a LinkedIn post format with:
- HOOK: A short, attention-grabbing first sentence (1-2 lines max)
- BODY: The main content with key points and value
- CTA: A call-to-action at the end (ask question, invite response, or encourage engagement)

Transcript:
{text}

Return ONLY a JSON object with keys: hook, body, cta. Keep each field concise."""

GENERATE_POST_PROMPT = """Transform the following draft into a polished LinkedIn post:

Draft:
{draft}

Rules:
- Start with a short, catchy hook
- Keep it conversational and authentic
- NO dashes, NO semicolons
- Use flowing sentences with commas
- End with a question or CTA to drive engagement
- Match this tone if provided: {tone}
"""

HOOK_SCORING_PROMPT = """You are an expert LinkedIn content strategist specializing in hook optimization.

Rate the following LinkedIn post hook on a scale of 1-10 for each criterion:

1. SCROLL_STOPPING (1-10): Does it immediately grab attention? Would someone stop scrolling?
2. CURIOSITY (1-10): Does it create curiosity gaps? Make readers want to learn more?
3. EMOTION (1-10): Does it evoke emotions (surprise, excitement, empathy, etc.)?
4. SPECIFICITY (1-10): Is it concrete and specific rather than vague/generic?
5. BREVITY (1-10): Is it concise? Can it be read in under 3 seconds?

HOOK TO EVALUATE:
"{hook}"

Respond ONLY with valid JSON in this exact format, no markdown, no code blocks:
{{
    "overall": <1-10 integer>,
    "scroll_stopping": <1-10 integer>,
    "curiosity": <1-10 integer>,
    "emotion": <1-10 integer>,
    "specificity": <1-10 integer>,
    "brevity": <1-10 integer>,
    "reasoning": "<2-3 sentence explanation of the overall score>",
    "improvements": ["<specific improvement 1>", "<specific improvement 2>", "<specific improvement 3>"]
}}"""

HOOK_VARIATION_PROMPT = """You are a LinkedIn content expert. Generate 3 different variations of the following hook, each with a distinct angle/strategy.

HOOK: "{hook}"

Create 3 variations that are:
- Scroll-stopping and attention-grabbing
- Concise (under 15 words each)
- Each with a different emotional angle or approach

Respond ONLY with valid JSON, no markdown:
{{
    "variations": [
        {{"text": "<variation 1>", "angle": "<emotional angle used>"}},
        {{"text": "<variation 2>", "angle": "<emotional angle used>"}},
        {{"text": "<variation 3>", "angle": "<emotional angle used>"}}
    ]
}}"""

TONE_EXTRACTION_PROMPT = """You are a LinkedIn content analyst. Analyze the following {num_posts} LinkedIn posts to extract a voice fingerprint.

For each dimension, provide a score from 0.0 to 1.0:
- VULNERABILITY: How much do they share personal struggles/failures/weaknesses?
- HUMOR: How often do they use jokes, wit, irony, or lighthearted moments?
- FORMALITY: How professional/corporate is the language vs casual/conversational?
- STORY_RATIO: What proportion of content is storytelling vs advice/tips?

Also identify:
- HOOK_STYLE: How do they start posts? (question, bold claim, story intro, contrarian, list, etc.)
- SIGNATURE_PHRASES: 3-5 recurring phrases or patterns that feel "them"
- EMOTIONAL_PALETTE: 5-7 emotions they typically evoke (e.g., inspiration, curiosity, nostalgia, empathy, excitement, etc.)
- COMMON_TOPICS: 5-7 recurring themes or topics
- VOICE_SIGNATURE: 2-3 sentence description of their unique voice
- TONE_SUMMARY: Brief summary of their overall tone

POSTS:
{posts_text}

Respond ONLY with valid JSON, no markdown:
{{
    "vulnerability": <0.0-1.0>,
    "humor": <0.0-1.0>,
    "formality": <0.0-1.0>,
    "story_ratio": <0.0-1.0>,
    "hook_style": "<primary hook style>",
    "signature_phrases": ["<phrase1>", "<phrase2>", "<phrase3>"],
    "emotional_palette": ["<emotion1>", "<emotion2>", "<emotion3>", "<emotion4>", "<emotion5>"],
    "common_topics": ["<topic1>", "<topic2>", "<topic3>", "<topic4>", "<topic5>"],
    "voice_signature": "<2-3 sentence voice description>",
    "tone_summary": "<brief tone summary>"
}}"""

TONE_GENERATION_PROMPT = """You are a LinkedIn content writer. Write a new LinkedIn post that matches the following voice fingerprint:

VOICE FINGERPRINT:
- Vulnerability: {vulnerability}
- Humor: {humor}
- Formality: {formality}
- Story Ratio: {story_ratio}
- Hook Style: {hook_style}
- Signature Phrases: {signature_phrases}
- Emotional Palette: {emotional_palette}
- Common Topics: {common_topics}
- Voice Signature: {voice_signature}
- Tone Summary: {tone_summary}

DRAFT CONTENT:
{draft}

Rewrite the draft into a polished LinkedIn post that:
- Uses the same hook style as their past posts
- Incorporates similar signature phrases naturally
- Matches the vulnerability, humor, formality, and story ratio levels
- Evokes emotions from their palette
- Stays on topic with their common themes
- Has their voice signature tone
- NEVER use dashes (-, –, —)
- NEVER use semicolons (;)
- Keep sentences flowing with commas, avoid excessive periods
- Start with a scroll-stopping hook matching their style

Respond ONLY with valid JSON:
{{"post": "<rewritten post>"}}"""


STYLE_COMPARISON_PROMPT = """You are a LinkedIn voice coach. Compare the user's voice fingerprint against {creator_name}'s profile.

USER PROFILE:
{user_profile}

{creator_name}'S PROFILE:
{creator_profile}

Analyze and provide:
1. GAPS: Dimensions where the user scores significantly lower (>=0.3 difference)
2. UNIQUE_TRAITS: What makes the user's voice unique vs {creator_name}
3. MISSING_TRAITS: Specific traits/techniques the user lacks
4. ACTIONS: 3 concrete actions to close the gaps (be specific)
5. ADOPTABLE_TRAITS: Dict of traits user could adopt with score 0.0-1.0 for each

Respond ONLY with valid JSON, no markdown:
{{
    "gaps": ["<dimension where gap exists>", "..."],
    "unique_traits": ["<what makes user unique>", "..."],
    "missing_traits": ["<specific missing trait>", "..."],
    "actions": ["<action 1>", "<action 2>", "<action 3>"],
    "adoptable_traits": {{
        "trait_name": <score 0.0-1.0>
    }}
}}"""
