# 📝 LinkedIn Post Generator

An AI-powered tool that transforms your drafts and raw thoughts into polished LinkedIn posts using your unique writing style.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation
```bash
git clone https://github.com/Khadejah14/sisu_chatbot2.git
cd sisu_chatbot2
pip install -r requirements.txt
Setup
Create .env file:

env
OPENAI_API_KEY=your_openai_api_key_here
Run the app:

bash
streamlit run app.py
💡 How to Use
1. Provide Your Content
Your LinkedIn Posts (1-6 examples): Paste existing posts separated by new lines

Your Drafts/Ramblings (1-6 drafts): Add raw thoughts separated by #

2. Save Inputs & Generate
Click "Save Inputs" to store your data

Choose number of posts (1-5)

Click "Generate" to create polished posts

🎯 Key Features
Style Learning: Analyzes your existing posts to maintain your unique voice

Draft Transformation: Converts raw thoughts into professional LinkedIn content

Smart Formatting: Automatic cleaning of dashes, semicolons, and excessive punctuation

Persistent Storage: Saves your inputs locally in data.json

📁 Project Structure
text
sisu_chatbot2/
├── app.py              # LinkedIn Post Generator
├── sisu_chatbot.py     # SISU Admissions Chatbot
├── data.json           # User data storage
├── .env               # Environment variables
└── requirements.txt   # Dependencies
🔧 Requirements
streamlit

openai

beautifulsoup4

requests

python-dotenv

⚠️ Notes
Always review generated content before posting
Keep your OpenAI API key secure
Data is stored locally for privacy

Keep your OpenAI API key secure

Data is stored locally for privacy
