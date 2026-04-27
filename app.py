"""Streamlit UI for LinkedIn Post Generator."""

import streamlit as st

from dotenv import load_dotenv
load_dotenv()

from features.post_generator import generate_posts, add_drafts
from features.hook_scorer import score_hook, generate_variations, score_variations, HookScore
from features.tone_analyzer import extract_profile, generate_with_profile, compare_drafts, ToneProfile
from features.voice_to_draft import clean_transcript, transcribe, structure, generate_post, add_to_drafts
from features.style_comparison import (
    compare_with_creator, get_creator_names, get_creator_profile, get_radar_data, StyleComparison
)
from utils import load_data, save_data, get_score_color


st.set_page_config(page_title="LinkedIn Post Generator", layout="wide")
st.title("LinkedIn Post Generator")


def main():
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Post Generator", "Hook Scorer", "Tone Analyzer", "Voice to Draft", "Style Comparison"]
    )

    with tab1:
        render_post_generator()
    with tab2:
        render_hook_scorer()
    with tab3:
        render_tone_analyzer()
    with tab4:
        render_voice_to_draft()
    with tab5:
        render_style_comparison()


def render_post_generator():
    data = load_data()
    
    st.header("Your LinkedIn Posts")
    my_posts_input = st.text_area(
        "Paste your posts (separated by new lines):",
        value="\n".join(data.get("my_posts", []))
    )
    
    st.header("Your Drafts")
    drafts_input = st.text_area(
        "Paste your drafts (separated by #):",
        value="#".join(data.get("drafts", []))
    )
    
    if st.button("Save Inputs"):
        data["my_posts"] = [p.strip() for p in my_posts_input.split("\n") if p.strip()]
        data["drafts"] = [d.strip() for d in drafts_input.split("#") if d.strip()]
        save_data(data)
        st.success("Saved!")
    
    st.header("Generate Posts")
    num_posts = st.number_input("Number of posts:", min_value=1, max_value=5, value=3)
    
    if st.button("Generate"):
        try:
            result = generate_posts(num_posts)
            st.text_area("Generated", result, height=400)
        except ValueError as e:
            st.error(str(e))


def render_hook_scorer():
    hook = st.text_area("Enter hook to score:", placeholder="I turned down a $200K salary...")
    
    col1, col2 = st.columns(2)
    with col1:
        score_btn = st.button("Score Hook", type="primary")
    with col2:
        vary_btn = st.button("Generate Variations")
    
    if score_btn and hook:
        with st.spinner("Scoring..."):
            score = score_hook(hook)
            render_hook_score(score)
    
    if vary_btn and hook:
        with st.spinner("Generating..."):
            vars = generate_variations(hook)
            scores = score_variations([v["text"] for v in vars])
            
            for i, (v, s) in enumerate(zip(vars, scores)):
                with st.expander(f"Variation {i+1}: {v['angle']}"):
                    st.text_area(f"var_{i}", v["text"], height=60)
                    color = get_score_color(s.overall)
                    st.markdown(f":{color}[**Score: {s.overall}/10**]")
    
    if "hook_score" in st.session_state:
        render_hook_score(st.session_state["hook_score"])


def render_hook_score(score: HookScore):
    c1, c2, c3 = st.columns(3)
    with c1:
        color = get_score_color(score.overall)
        st.markdown(f"### Overall: :{color}[{score.overall}/10]")
    
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
            color = get_score_color(val)
            st.markdown(f"**{label}:** :{color}[{val}/10]")
    
    st.markdown(f"**Reasoning:** {score.reasoning}")
    if score.improvements:
        st.markdown("**Improvements:**")
        for imp in score.improvements:
            st.markdown(f"- {imp}")


def render_tone_analyzer():
    posts_input = st.text_area(
        "Paste 3-10 posts (separated by #):",
        placeholder="Post 1...\n#\nPost 2...\n#\nPost 3..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        extract_btn = st.button("Extract Voice", type="primary")
    with col2:
        generate_btn = st.button("Generate with Tone")
    
    if extract_btn and posts_input:
        posts = [p.strip() for p in posts_input.split("#") if p.strip()]
        if len(posts) < 3 or len(posts) > 10:
            st.error("Provide 3-10 posts")
            return
        
        with st.spinner("Analyzing..."):
            profile = extract_profile(posts)
            st.session_state["tone_profile"] = profile
    
    if "tone_profile" in st.session_state:
        profile = st.session_state["tone_profile"]
        render_tone_profile(profile)
    
    if generate_btn and posts_input:
        posts = [p.strip() for p in posts_input.split("#") if p.strip()]
        if len(posts) < 3 or len(posts) > 10:
            st.error("Provide 3-10 posts")
            return
        
        draft = st.text_input("Draft to rewrite:")
        if draft and "tone_profile" in st.session_state:
            with st.spinner("Generating..."):
                result = generate_with_profile(draft, st.session_state["tone_profile"])
                st.text_area("Generated", result, height=200)


def render_tone_profile(profile: ToneProfile):
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
    
    with st.expander("Voice Signature"):
        st.write(profile.voice_signature)


def render_voice_to_draft():
    method = st.radio("Input", ["Record", "Upload"], horizontal=True)
    
    audio_data = None
    if method == "Record":
        audio = st.audio_input("Record")
        if audio:
            audio_data = audio.getvalue()
    else:
        uploaded = st.file_uploader("Upload (mp3, wav, m4a)", type=["mp3", "wav", "m4a"])
        if uploaded:
            audio_data = uploaded.getvalue()
    
    if audio_data:
        size_mb = len(audio_data) / (1024 * 1024)
        st.info(f"File size: {size_mb:.2f} MB")
        
        if size_mb > 25:
            st.error("File too large (max 25MB)")
            return
        
        progress = st.progress(0)
        
        progress.progress(25)
        transcript = transcribe(audio_data)
        st.session_state["voice_transcript"] = transcript
        
        progress.progress(50)
        cleaned = clean_transcript(transcript)
        progress.progress(100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Raw", transcript, height=150)
        with col2:
            st.text_area("Cleaned", cleaned, height=150)
        
        if st.button("Structure"):
            structured = structure(cleaned)
            st.session_state["structured_draft"] = structured
    
    if "structured_draft" in st.session_state:
        draft = st.session_state["structured_draft"]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_area("Hook", draft.get("hook", ""), height=80)
        with c2:
            st.text_area("Body", draft.get("body", ""), height=80)
        with c3:
            st.text_area("CTA", draft.get("cta", ""), height=80)
        
        full_draft = f"{draft.get('hook', '')}\n\n{draft.get('body', '')}\n\n{draft.get('cta', '')}"
        
        col_add, col_gen = st.columns(2)
        with col_add:
            if st.button("Add to Drafts"):
                add_to_drafts(full_draft)
                st.success("Added!")
        with col_gen:
            if st.button("Generate Post"):
                with st.spinner("Generating..."):
                    post = generate_post(full_draft)
                    st.session_state["generated_post"] = post
    
    if "generated_post" in st.session_state:
        st.text_area("Generated Post", st.session_state["generated_post"], height=200)
        if st.button("Save Generated"):
            add_to_drafts(st.session_state["generated_post"])
            st.success("Saved!")


def render_style_comparison():
    from features.tone_analyzer import ToneProfile

    st.header("Style Comparison")
    st.caption("Compare your voice against top LinkedIn creators")

    creators = get_creator_names()
    selected_creator = st.selectbox("Select a creator to compare with:", creators)

    if st.button("Compare My Style", type="primary"):
        if "tone_profile" not in st.session_state:
            st.error("Extract your voice profile first in the Tone Analyzer tab")
            return

        user_profile = st.session_state["tone_profile"].to_dict()

        with st.spinner(f"Comparing with {selected_creator}..."):
            comparison = compare_with_creator(user_profile, selected_creator)
            st.session_state["style_comparison"] = comparison

    if "style_comparison" in st.session_state:
        comparison = st.session_state["style_comparison"]

        # Radar chart
        radar_data = get_radar_data(comparison.user_profile, comparison.creator_profile)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Dimension Comparison")
            try:
                import plotly.graph_objects as go

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=radar_data["user_values"] + [radar_data["user_values"][0]],
                    theta=radar_data["dimensions"] + [radar_data["dimensions"][0]],
                    fill='toself',
                    name='You'
                ))
                fig.add_trace(go.Scatterpolar(
                    r=radar_data["creator_values"] + [radar_data["creator_values"][0]],
                    theta=radar_data["dimensions"] + [radar_data["dimensions"][0]],
                    fill='toself',
                    name=comparison.creator_name
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=True,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                for dim, user_val, creator_val in zip(
                    radar_data["dimensions"], radar_data["user_values"], radar_data["creator_values"]
                ):
                    st.text(f"{dim.title()}: You {user_val:.1f} vs {comparison.creator_name} {creator_val:.1f}")
                    st.progress(creator_val, text=f"Target: {creator_val:.1f}")

        with col2:
            st.subheader("Gaps")
            for gap in comparison.gaps:
                st.warning(f"**{gap}**")

            st.subheader("Your Unique Traits")
            for trait in comparison.unique_traits[:3]:
                st.success(f"✓ {trait}")

            st.subheader("Missing Traits")
            for trait in comparison.missing_traits[:3]:
                st.error(f"✗ {trait}")

        st.divider()

        st.subheader("3 Actions to Close Gaps")
        for i, action in enumerate(comparison.actions, 1):
            st.markdown(f"**{i}.** {action}")

        st.divider()

        st.subheader("Adopt This Trait")
        st.caption("Inject creator traits into your post generation")

        adoptable = comparison.adoptable_traits
        if adoptable:
            cols = st.columns(len(adoptable))
            for i, (trait, score) in enumerate(adoptable.items()):
                with cols[i]:
                    if st.button(f"Adopt: {trait}", key=f"adopt_{trait}"):
                        if "adopted_traits" not in st.session_state:
                            st.session_state["adopted_traits"] = {}
                        st.session_state["adopted_traits"][trait] = score
                        st.success(f"Added {trait} to your profile!")

        if "adopted_traits" in st.session_state and st.session_state["adopted_traits"]:
            st.info(f"**Adopted traits:** {', '.join(st.session_state['adopted_traits'].keys())}")
            if st.button("Clear Adopted Traits"):
                st.session_state["adopted_traits"] = {}
                st.rerun()


if __name__ == "__main__":
    main()