"""Competitor Tracker Streamlit UI."""

import streamlit as st
import json
import pandas as pd
from datetime import datetime

from competitor_tracker import CompetitorTracker, get_stats

st.set_page_config(
    page_title="Competitor Tracker",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "tracker" not in st.session_state:
    st.session_state.tracker = CompetitorTracker(use_mock=True)

if "user_hooks" not in st.session_state:
    st.session_state.user_hooks = []

if "user_topics" not in st.session_state:
    st.session_state.user_topics = []

tracker = st.session_state.tracker


def render_competitor_card(competitor: dict) -> None:
    with st.container():
        cols = st.columns([3, 1, 1, 1])
        with cols[0]:
            st.subheader(competitor.get("name", "Unknown"))
            st.caption(f"Industry: {competitor.get('industry', 'N/A')}")
        with cols[1]:
            st.metric("Followers", f"{competitor.get('followers', 0):,}")
        with cols[2]:
            st.metric("Posts", competitor.get("post_count", 0))
        with cols[3]:
            st.metric("Likes", f"{competitor.get('total_likes', 0):,}")
        st.divider()


def render_top_posts_table(posts: list[dict]) -> None:
    if not posts:
        st.info("No posts available yet. Scrape competitors first.")
        return
    
    df = pd.DataFrame(posts)
    
    display_cols = ["competitor_name", "hook", "likes", "comments", "shares", "posted_at"]
    available_cols = [c for c in display_cols if c in df.columns]
    
    st.dataframe(
        df[available_cols],
        use_container_width=True,
        hide_index=True,
    )


def render_trend_insights(insights: dict) -> None:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Hook Types")
        if insights.get("top_hook_types"):
            for hook_type, count in insights["top_hook_types"]:
                st.progress(count / insights["total_analyzed"], text=f"{hook_type}: {count}")
    
    with col2:
        st.subheader("Top Topics")
        if insights.get("top_topics"):
            for topic, count in insights["top_topics"][:5]:
                st.progress(count / insights["total_analyzed"], text=f"{topic}: {count}")
    
    st.divider()
    
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Tone Distribution")
        if insights.get("top_tones"):
            for tone, count in insights["top_tones"]:
                st.progress(count / insights["total_analyzed"], text=f"{tone}: {count}")
    
    with col4:
        st.subheader("Viral Patterns")
        if insights.get("viral_patterns"):
            for pattern, count in insights["viral_patterns"]:
                st.progress(count / insights["total_analyzed"], text=f"{pattern}: {count}")


def render_gap_analysis(gaps: list) -> None:
    if not gaps:
        st.info("No gaps found. Add your topics first.")
        return
    
    for i, gap in enumerate(gaps):
        with st.expander(f"{gap.topic} - Score: {gap.opportunity_score:.1%}"):
            st.markdown(f"**Angle:** {gap.angle}")
            st.markdown(f"**{gap.description}**")
            
            if gap.competitor_examples:
                st.markdown("**Competitor Examples:**")
                for ex in gap.competitor_examples[:3]:
                    st.caption(f"- {ex}")


def render_hook_variation(hook: str) -> None:
    cols = st.columns([3, 1])
    
    with cols[0]:
        st.text_area("Original Hook", hook, height=80)
    
    with cols[1]:
        st.write("")
        st.write("")
        generate_btn = st.button("Steal This Hook", type="primary", key="gen_hook")
    
    if generate_btn and hook:
        user_hooks = st.session_state.get("user_hooks", [])
        
        variations = tracker.generate_hook_variation(
            hook, 
            user_hooks=user_hooks if user_hooks else None
        )
        
        for i, var in enumerate(variations):
            with st.expander(f"Variation {i+1}"):
                st.text_area(f"var_{i}", var.get("text", var if isinstance(var, str) else ""), height=80)
                st.caption(f"Angle: {var.get('angle', 'N/A')}")


st.title("Competitor Tracker")
st.caption("Analyze competitor LinkedIn posts, find gaps, and steal winning hooks")

with st.sidebar:
    st.header("Settings")
    
    use_mock = st.toggle("Demo Mode (Mock Data)", value=True)
    if use_mock != (st.session_state.tracker.use_mock if "tracker" in st.session_state else True):
        st.session_state.tracker = CompetitorTracker(use_mock=use_mock)
        tracker = st.session_state.tracker
    
    st.divider()
    
    st.subheader("Your Content")
    user_topics_input = st.text_area(
        "Topics you post about (one per line)",
        value="\n".join(st.session_state.user_topics),
        height=100,
        key="user_topics_input",
    )
    
    user_hooks_input = st.text_area(
        "Your hooks (one per line)",
        value="\n".join(st.session_state.user_hooks),
        height=100,
        key="user_hooks_input",
    )
    
    if st.button("Save Content Profile"):
        st.session_state.user_topics = [t.strip() for t in user_topics_input.split("\n") if t.strip()]
        st.session_state.user_hooks = [h.strip() for h in user_hooks_input.split("\n") if h.strip()]
        tracker.set_user_topics(st.session_state.user_topics)
        st.success("Saved!")
    
    st.divider()
    
    st.subheader("Competitor Management")
    
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Name")
    with col2:
        new_url = st.text_input("Profile URL")
    
    new_industry = st.text_input("Industry")
    
    if st.button("Add Competitor"):
        if new_name and new_url:
            tracker.add_competitor(new_name, new_url, new_industry)
            st.success(f"Added {new_name}")
            st.rerun()
    
    st.divider()
    
    st.subheader("Scrape")
    
    scrape_limit = st.slider("Posts per competitor", 1, 20, 10)
    
    scrape_col1, scrape_col2 = st.columns(2)
    with scrape_col1:
        scrape_all_btn = st.button("Scrape All", type="primary")
    with scrape_col2:
        refresh_btn = st.button("Refresh Data")


if scrape_all_btn:
    with st.spinner("Scraping competitors..."):
        result = tracker.scrape_all_competitors(scrape_limit)
        st.success(f"Scraped {result['total_posts']} posts from {result['success']} competitors")
        st.rerun()


if refresh_btn:
    st.rerun()


tab1, tab2, tab3, tab4 = st.tabs(["Competitors", "Top Posts", "Gap Analysis", "Hook Generator"])


with tab1:
    st.subheader("Tracked Competitors")
    
    competitors = tracker.get_competitors_data()
    
    if not competitors:
        st.info("No competitors tracked yet. Add some in the sidebar.")
    else:
        for comp in competitors:
            render_competitor_card(comp)
        
        stats = tracker.get_stats()
        
        st.divider()
        st.subheader("Overview")
        
        ocol1, ocol2, ocol3, ocol4 = st.columns(4)
        with ocol1:
            st.metric("Competitors", stats["competitors_count"])
        with ocol2:
            st.metric("Total Posts", stats["posts_count"])
        with ocol3:
            st.metric("Total Likes", f"{stats['total_likes']:,}")
        with ocol4:
            st.metric("Total Comments", f"{stats['total_comments']:,}")


with tab2:
    st.subheader("Top Performing Posts")
    
    top_posts = tracker.get_top_posts_data(limit=15)
    render_top_posts_table(top_posts)
    
    st.divider()
    
    st.subheader("Trend Insights")
    insights = tracker.get_trend_insights()
    render_trend_insights(insights)


with tab3:
    st.subheader("Gap Analysis")
    
    st.markdown("### What topics/angles are you missing?")
    
    user_topics = st.session_state.get("user_topics", [])
    user_hooks = st.session_state.get("user_hooks", [])
    
    gaps = tracker.get_gap_analysis(user_topics, user_hooks)
    render_gap_analysis(gaps)
    
    st.divider()
    
    st.subheader("All Trends")
    trends = tracker.get_trends_data()
    if trends:
        trend_df = pd.DataFrame(trends)
        st.dataframe(
            trend_df[["trend_name", "frequency", "last_seen"]],
            use_container_width=True,
            hide_index=True,
        )


with tab4:
    st.subheader("Steal This Hook")
    
    st.markdown("Paste a competitor hook to generate variations in your voice:")
    
    hook_input = st.text_area(
        "Competitor Hook",
        placeholder="I turned down a $200K salary to join a startup...",
        height=100,
    )
    
    if hook_input:
        render_hook_variation(hook_input)
    
    st.divider()
    
    st.markdown("### Recent Scrape Logs")
    logs = tracker.get_scrape_logs_data(limit=10)
    if logs:
        for log in logs:
            status_icon = "✅" if log["status"] == "success" else "❌"
            st.caption(f"{status_icon} {log['competitor_name']}: {log['posts_fetched']} posts - {log['created_at']}")