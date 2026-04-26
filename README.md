# LinkedIn Post Generator

AI-powered tool that transforms your drafts and raw thoughts into polished LinkedIn posts using your unique writing style.

## Features

### 1. Post Generator
- Paste existing LinkedIn posts (1-6 examples) to learn your style
- Add raw drafts/ramblings separated by `#`
- Generate 1-5 polished posts maintaining your voice

### 2. Hook Scoring & Optimization
- Score hooks on: Scroll-Stopping, Curiosity, Emotion, Specificity, Brevity
- Generate 3 variations with angle (contrarian, story, question, etc.)
- Detailed scoring with improvement suggestions

### 3. Tone Analyzer
- Extract voice fingerprint from 3-10 past posts
- Analyze: Vulnerability, Humor, Formality, Story Ratio
- Identify hook style, signature phrases, emotional palette
- Visual radar chart
- Generate tone-matched posts

### 4. Voice to Draft
- Record audio (Streamlit audio_input) or upload files (mp3, wav, m4a)
- Transcribe via OpenAI Whisper API
- Auto-clean filler words (um, uh, like, basically, etc.)
- Structure into Hook/Body/CTA format
- Generate polished LinkedIn post
- Save directly to drafts

## Quick Start

```bash
git clone https://github.com/Khadejah14/sisu_chatbot2.git
cd sisu_chatbot2
pip install -r requirements.txt
```

Create `.env` file:
```
OPENAI_API_KEY=sk-your-openai-api-key
```

Run the app:
```bash
streamlit run app.py
```

## Requirements

- streamlit
- openai
- beautifulsoup4
- requests
- python-dotenv
- plotly
- pandas

## Project Structure

```
AutoPosts/
├── app.py                      # Main Streamlit app
├── voice_to_draft.py           # Voice transcription module
├── hook_scorer.py             # Hook scoring & variations
├── tone_analyzer.py           # Voice fingerprint extraction
├── base.py                   # Base classes
├── registry.py               # Module registry
├── data.json                # User data storage
├── .env                     # Environment variables
├── requirements.txt         # Dependencies
├── competitor_tracker/        # Competitor tracking module
│   ├── analyzer.py
│   ├── database.py
│   ├── gap_analyzer.py
│   ├── scraper.py
│   └── tracker.py
├── versions/                # Post version templates
└── __init__.py
```