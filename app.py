import streamlit as st
import json
import os
import requests
from openai import OpenAI
from bs4 import BeautifulSoup
import re

# Initialize GPT API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    "Paste your posts here (one per line, first sentence is your hook style):",
    value="\n".join(data.get("my_posts", []))
)

st.header("Your Drafts / Ramblings (up to 6, separate with #)")
drafts_input = st.text_area(
    "Paste your drafts or raw thoughts here, separate each draft with a #:",
    value="#".join(data.get("drafts", []))
)

st.header("Optional: Content You Like (Articles/blogs links)")
content_input = st.text_area(
    "Paste links here (one per line):",
    value="\n".join(data.get("content_links", []))
)

if st.button("Save Inputs"):
    data["my_posts"] = [p.strip() for p in my_posts_input.split("\n") if p.strip()]
    data["drafts"] = [d.strip() for d in drafts_input.split("#") if d.strip()]
    data["content_links"] = [c.strip() for c in content_input.split("\n") if c.strip()]
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

3. Content I like (articles/YouTube/blogs), summarized below (use as knowledge, optional):
{combined_content}

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

