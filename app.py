import streamlit as st
import json
import os
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import re

from hook_scorer import HookScorer, HookScore
from tone_analyzer import ToneAnalyzer, ToneProfile

# Initialize GPT API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
scorer = HookScorer()
tone_analyzer = ToneAnalyzer()

DATA_FILE = "data.json"

# Load or initialize data
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
else:
    data = {"my_posts": [], "drafts": [], "content_links": []}

# --- Helper to fetch article content ---
def fetch_content(url):
    try:
        r = requests.get(url, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text() for p in paragraphs])
        return text[:2000]  # limit to first 2000 chars
    except:
        return ""

# --- Helper to clean text ---
def clean_text(text):
    text = re.sub(r"[-–—;]", "", text)  # Remove dashes and semicolons
    text = re.sub(r"\.{2,}", ".", text)  # Remove excessive periods
    return text

# --- Streamlit UI ---
st.title("LinkedIn Post Generator")

st.header("Your LinkedIn Posts (up to 6)")
my_posts_input = st.text_area(
    "Paste your posts here and seperate them with # (one per line, first sentence is your hook style):",
    value="\n".join(data.get("my_posts", []))
)

st.header("Your Drafts / Ramblings (up to 6, separate with #)")
drafts_input = st.text_area(
    "Paste your drafts or raw thoughts here, separate each draft with a #:",
    value="#".join(data.get("drafts", []))
)



if st.button("Save Inputs"):
    data["my_posts"] = [p.strip() for p in my_posts_input.split("\n") if p.strip()]
    data["drafts"] = [d.strip() for d in drafts_input.split("#") if d.strip()]
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    st.success("Inputs saved!")

st.header("Generate Posts")
num_posts = st.number_input("Number of posts to generate:", min_value=1, max_value=5, value=3)

if st.button("Generate"):
    if not data["my_posts"]:
        st.error("Please add your LinkedIn posts first!")
    elif not data["drafts"]:
        st.error("Please add at least one draft!")
    else:
        # Fetch summaries from links
        st.info("Fetching content from links...")
        content_texts = []
        for url in data["content_links"]:
            content_texts.append(fetch_content(url))
        combined_content = "\n".join(content_texts) if content_texts else "No content links provided."

        # Prepare prompt for GPT
        prompt = f"""
You are a LinkedIn content assistant. I will provide:

1. My previous LinkedIn posts (this is my style and tone, including hooks):
{data['my_posts']}

2. My raw drafts or ramblings (rewrite these into polished LinkedIn posts):
{data['drafts']}

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

        with st.spinner("Generating posts..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            generated_text = response.choices[0].message.content
            cleaned_output = clean_text(generated_text)
            st.subheader("Generated Posts")
            st.text_area("Output", cleaned_output, height=400)


st.divider()
st.header("Hook Scoring & Optimization")

hook_input = st.text_area(
    "Enter your LinkedIn post hook to score:",
    placeholder="I turned down a $200K salary to join a startup...",
    help="Enter just the hook line (first sentence of your post)"
)

col1, col2 = st.columns(2)
with col1:
    generate_variations = st.button("Generate 3 Variations & Score All", type="primary")
with col2:
    score_only = st.button("Score Hook Only")

def get_score_color(score: int) -> str:
    if score >= 7:
        return "green"
    elif score >= 4:
        return "yellow"
    else:
        return "red"

def render_score_badge(label: str, score: int) -> None:
    color = get_score_color(score)
    st.markdown(f"**{label}:** :{color}[{score}/10]")

def render_score_section(score: HookScore, title: str = "Score Results") -> None:
    st.subheader(title)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        overall_color = get_score_color(score.overall)
        st.markdown(f"### Overall: :{overall_color}[{score.overall}/10]")
    with col2:
        st.markdown("**Criteria Breakdown:**")
    with col3:
        st.empty()
    
    cols = st.columns(5)
    criteria = [
        ("Scroll-Stopping", score.scroll_stopping),
        ("Curiosity", score.curiosity),
        ("Emotion", score.emotion),
        ("Specificity", score.specificity),
        ("Brevity", score.brevity),
    ]
    for col, (label, val) in zip(cols, criteria):
        with col:
            render_score_badge(label, val)
    
    st.markdown("---")
    st.markdown(f"**Reasoning:** {score.reasoning}")
    
    if score.improvements:
        st.markdown("**Suggested Improvements:**")
        for imp in score.improvements:
            st.markdown(f"- {imp}")

if score_only and hook_input.strip():
    with st.spinner("Scoring hook..."):
        try:
            score = scorer.score_hook(hook_input.strip())
            st.session_state["hook_score"] = score
            st.session_state["variations"] = None
        except Exception as e:
            st.error(f"Error: {e}")

if generate_variations and hook_input.strip():
    with st.spinner("Generating variations and scoring..."):
        try:
            variations = scorer.generate_variations(hook_input.strip())
            st.session_state["variations"] = variations
            st.session_state["variation_scores"] = scorer.score_variations([v["text"] for v in variations])
            st.session_state["hook_score"] = None
        except Exception as e:
            st.error(f"Error: {e}")

if "variations" in st.session_state and st.session_state["variations"]:
    st.subheader("Variations")
    cols = st.columns(3)
    best_idx = 0
    best_score = 0
    
    for i, (var, score) in enumerate(zip(st.session_state["variations"], st.session_state["variation_scores"])):
        with cols[i]:
            angle_color = get_score_color(score.overall)
            st.markdown(f"**Variation {i+1}** (*{var['angle']}*)")
            st.markdown(f":{angle_color}[**Score: {score.overall}/10**]")
            st.text_area(f"var_{i}", var["text"], height=80, key=f"var_area_{i}", label_visibility="collapsed")
            
            with st.expander("See detailed score"):
                render_score_section(score, f"Variation {i+1} Details")
            
            if score.overall > best_score:
                best_score = score.overall
                best_idx = i
    
    if st.button(f"Select Variation {best_idx + 1} as Best", type="primary"):
        st.session_state["selected_hook"] = st.session_state["variations"][best_idx]["text"]
        st.success(f"Selected Variation {best_idx + 1} with score {best_score}/10!")

if "hook_score" in st.session_state and st.session_state["hook_score"]:
    render_score_section(st.session_state["hook_score"])

if "selected_hook" in st.session_state and st.session_state["selected_hook"]:
    st.divider()
    st.subheader("Selected Hook")
    st.success(st.session_state["selected_hook"])
    if st.button("Copy to Clipboard"):
        st.code(st.session_state["selected_hook"])
        st.info("Copy the text above manually (Streamlit doesn't support clipboard API)")


st.divider()
st.header("Tone Analyzer")

tone_posts_input = st.text_area(
    "Paste 3-10 past LinkedIn posts to analyze (separate with #):",
    placeholder="Post 1...\n---\nPost 2...\n---\nPost 3...",
    key="tone_posts",
)

col1, col2 = st.columns(2)
with col1:
    extract_btn = st.button("Extract Voice Fingerprint", type="primary")
with col2:
    generate_btn = st.button("Generate with Tone")


if extract_btn and tone_posts_input.strip():
    posts = [p.strip() for p in tone_posts_input.split("#") if p.strip()]
    if len(posts) < 3 or len(posts) > 10:
        st.error("Please provide between 3 and 10 posts")
    else:
        with st.spinner("Analyzing tone..."):
            try:
                profile = tone_analyzer.extract_profile(posts)
                st.session_state["tone_profile"] = profile
                st.session_state["tone_generated"] = None
            except Exception as e:
                st.error(f"Error: {e}")


if "tone_profile" in st.session_state and st.session_state["tone_profile"]:
    profile = st.session_state["tone_profile"]
    
    st.subheader("Voice Fingerprint")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Tone Dimensions**")
        st.progress(profile.vulnerability, text=f"Vulnerability: {profile.vulnerability:.1f}")
        st.progress(profile.humor, text=f"Humor: {profile.humor:.1f}")
        st.progress(profile.formality, text=f"Formality: {profile.formality:.1f}")
        st.progress(profile.story_ratio, text=f"Story Ratio: {profile.story_ratio:.1f}")
    with c2:
        st.markdown(f"**Hook Style:** {profile.hook_style}")
        st.markdown("**Signature Phrases:**")
        for phrase in profile.signature_phrases:
            st.markdown(f"- {phrase}")
    
    with st.expander("Emotional Palette"):
        st.write(", ".join(profile.emotional_palette))
    
    with st.expander("Common Topics"):
        for topic in profile.common_topics:
            st.markdown(f"- {topic}")
    
    with st.expander("Voice Signature"):
        st.write(profile.voice_signature)
    
    with st.expander("Tone Summary"):
        st.write(profile.tone_summary)
    
    st.markdown("---")
    st.markdown("**Radar Chart**")
    try:
        import plotly.graph_objects as go
        categories = ["Vulnerability", "Humor", "Formality", "Story Ratio"]
        values = [profile.vulnerability, profile.humor, profile.formality, profile.story_ratio]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Tone Profile'
        ))
        fig.update_layout(
            polar=dict(radial=dict(angularaxis=dict(rotation=90))),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("Install plotly for radar chart: pip install plotly")


if generate_btn and tone_posts_input.strip():
    posts = [p.strip() for p in tone_posts_input.split("#") if p.strip()]
    if len(posts) < 3 or len(posts) > 10:
        st.error("Please provide between 3 and 10 posts")
    else:
        with st.spinner("Extracting profile and generating..."):
            try:
                profile = tone_analyzer.extract_profile(posts)
                st.session_state["tone_profile"] = profile
                
                draft = st.session_state.get("tone_draft", "")
                if not draft:
                    draft = st.text_input("Enter draft content to rewrite:", key="draft_input")
                    st.session_state["tone_draft"] = draft
                
                if draft:
                    generated = tone_analyzer.generate_with_profile(draft, profile)
                    st.session_state["tone_generated"] = generated
            except Exception as e:
                st.error(f"Error: {e}")


if "tone_generated" in st.session_state and st.session_state["tone_generated"]:
    st.divider()
    st.subheader("Before / After Comparison")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Original Draft**")
        original = st.session_state.get("tone_draft", "")
        st.text_area("Before", original, height=200, key="before_area")
    with col2:
        st.markdown("**Tone-Adjusted**")
        st.text_area("After", st.session_state["tone_generated"], height=200, key="after_area")
    
    with st.expander("See Analysis"):
        try:
            comparison = tone_analyzer.compare_drafts(original, st.session_state["tone_generated"])
            st.markdown("**Improvements:**")
            for imp in comparison.get("improvements", []):
                st.markdown(f"- {imp}")
            st.markdown("**Changes:**")
            for chg in comparison.get("changes", []):
                st.markdown(f"- {chg}")
            st.markdown(f"**Readability Improvement:** {comparison.get('readability_improvement', 0)}%")
        except:
            pass

