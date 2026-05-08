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
- Generate polished LinkedIn Post
- Save directly to drafts

### 5. Style Comparison
- Compare your writing style against competitors or industry leaders
- Identify gaps and opportunities for differentiation

### 6. Competitor Tracker
- Track competitor LinkedIn posts and engagement
- Analyze posting patterns and content strategies
- Identify content gaps with gap analysis
- Separate Streamlit app interface (`competitor_tracker_app.py`)

### 7. Services Layer
- **Post Service**: Orchestrates post generation workflow (tone analysis → post generation → hook scoring)
- **Analysis Service**: Combines tone analysis with style comparison across multiple creators
- Enables API integration for programmatic access

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      UI LAYER                           │
│  ┌──────────────────┐    ┌───────────────────────────┐  │
│  │  Streamlit App   │    │   FastAPI Backend         │  │
│  │  (app.py)        │    │   (backend/main.py)       │  │
│  └────────┬─────────┘    └─────────────┬─────────────┘  │
├───────────┼────────────────────────────┼────────────────┤
│           │         API LAYER          │                │
│           │    ┌──────────────────┐    │                │
│           └───►│  Routes          │◄───┘                │
│                │  /api/optimize   │                     │
│                │  /api/analyze    │                     │
│                │  /api/workspace  │                     │
│                └────────┬─────────┘                     │
├─────────────────────────┼───────────────────────────────┤
│                  SERVICES LAYER                         │
│           ┌─────────────┴──────────────┐                │
│           ▼                            ▼                │
│  ┌─────────────────┐    ┌──────────────────────┐        │
│  │  Post Service   │    │  Analysis Service    │        │
│  │  optimize_post  │    │  analyze_voice       │        │
│  │  batch_optimize │    │  compare_creators    │        │
│  └────────┬────────┘    └──────────┬───────────┘        │
├───────────┼────────────────────────┼────────────────────┤
│                   FEATURES LAYER                        │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────┐  │
│  │  Post    │ │  Hook    │ │   Tone    │ │  Voice   │  │
│  │ Generator│ │  Scorer  │ │  Analyzer │ │to Draft  │  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └────┬─────┘  │
│       │            │             │             │        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              llm.py (OpenAI Client)              │   │
│  └──────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                     STORAGE                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   SQLite     │  │  JSON File   │  │  In-Memory   │  │
│  │  (database/) │  │  (data/)     │  │  Cache       │  │
│  │  users/posts │  │  drafts      │  │  (utils/)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Data Flow:**
```
User Input → UI (Streamlit / API) → Services → Features → LLM (OpenAI)
                                        ↓
                              Cache ← Response → SQLite / JSON
```

## Quick Start

```bash
git clone https://github.com/Khadejah14/AutoPosts.git
cd AutoPosts
pip install -r requirements.txt
```

Create `.env` file:
```
OPENAI_API_KEY=sk-your-openai-api-key
```

Run the main app:
```bash
streamlit run app.py
```

Run the competitor tracker app:
```bash
streamlit run competitor_tracker_app.py
```

## Requirements

- streamlit
- openai
- requests
- beautifulsoup4
- plotly
- python-dotenv
- pandas

## Project Structure

```
AutoPosts/
├── app.py                      # Main Streamlit app
├── competitor_tracker_app.py   # Competitor tracker Streamlit app
├── config.py                   # Configuration settings
├── llm.py                      # LLM integration utilities
├── utils.py                    # Utility functions
├── core/                       # Core framework
│   ├── __init__.py
│   ├── base.py                 # Base classes
│   └── registry.py             # Module registry
├── features/                   # Feature modules (independent)
│   ├── __init__.py
│   ├── hook_scorer.py         # Hook scoring & variations
│   ├── post_generator.py      # Post generation logic
│   ├── style_comparison.py    # Style comparison tool
│   ├── tone_analyzer.py       # Voice fingerprint extraction
│   └── voice_to_draft.py      # Voice transcription module
├── services/                   # Service layer (orchestrates features)
│   ├── __init__.py
│   ├── post_service.py        # Post generation workflow
│   └── analysis_service.py    # Voice analysis & style comparison
├── competitor_tracker/         # Competitor tracking module
│   ├── __init__.py
│   ├── analyzer.py            # Content analysis
│   ├── database.py            # SQLite database
│   ├── gap_analyzer.py        # Content gap analysis
│   ├── scraper.py             # LinkedIn scraping
│   └── tracker.py             # Competitor tracking logic
├── versions/                   # Post version templates
│   ├── __init__.py
│   ├── v1_hook_focus.json
│   ├── v2_storytelling.json
│   └── v3_contrarian.json
├── data/                       # User data storage
│   └── data.json
├── .env                        # Environment variables
├── requirements.txt            # Dependencies
└── Dockerfile                  # Docker configuration
```
