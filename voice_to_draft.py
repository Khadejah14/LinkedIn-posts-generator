import os
import re
import io
import json
import tempfile
import streamlit as st
from openai import OpenAI
from typing import List, Tuple

def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_FILE_SIZE = 25 * 1024 * 1024

FILLER_WORDS = [
    r"\b(um|uh|er|ah|like|you know|basically|actually|seriously|honestly)\b",
    r"\b(i mean|i guess|i think|i know right|i'll be like|i'm just saying)\b",
    r"\b(yeah|no|okay|right|so|well|then|you know)\b",
]

def clean_filler_words(text: str) -> str:
    text = text.lower()
    for pattern in FILLER_WORDS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(s)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.+", ".", text)
    text = re.sub(r",+", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r"([.,!?])\s+([.,!?])", r"\1\2", text)
    text = text.strip()
    return text

def fix_runons(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    cleaned = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 1:
            sent = sent[0].upper() + sent[1:] if sent[0].islower() else sent
            cleaned.append(sent)
    return " ".join(cleaned)

def clean_transcript(text: str) -> str:
    text = clean_filler_words(text)
    text = fix_runons(text)
    return text

def split_audio_if_needed(audio_data: bytes) -> List[bytes]:
    if len(audio_data) <= MAX_FILE_SIZE:
        return [audio_data]
    
    parts = []
    num_parts = (len(audio_data) // MAX_FILE_SIZE) + 1
    part_size = len(audio_data) // num_parts
    
    for i in range(num_parts):
        start = i * part_size
        end = min((i + 1) * part_size, len(audio_data))
        parts.append(audio_data[start:end])
    
    return parts

def transcribe_audio(audio_data: bytes, filename: str = "audio.mp3") -> str:
    client = get_openai_client()
    parts = split_audio_if_needed(audio_data)
    
    if len(parts) > 1:
        transcripts = []
        for i, part in enumerate(parts):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_part{i}.mp3") as tmp:
                tmp.write(part)
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                    transcripts.append(response)
            finally:
                os.unlink(tmp_path)
        
        full_transcript = " ".join(transcripts)
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        try:
            with open(tmp_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                full_transcript = response
        finally:
            os.unlink(tmp_path)
    
    return full_transcript

def structure_draft(text: str) -> dict:
    client = get_openai_client()
    prompt = f"""Analyze the following transcript and structure it into a LinkedIn post format with:
- HOOK: A short, attention-grabbing first sentence (1-2 lines max)
- BODY: The main content with key points and value
- CTA: A call-to-action at the end (ask question, invite response, or encourage engagement)

Transcript:
{text}

Return ONLY a JSON object with keys: hook, body, cta. Keep each field concise."""


    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    structured = json.loads(response.choices[0].message.content)
    return structured

def generate_post_from_draft(draft: str, tone_profile: dict = None) -> str:
    client = get_openai_client()
    prompt = f"""Transform the following draft into a polished LinkedIn post:

Draft:
{draft}

Rules:
- Start with a short, catchy hook
- Keep it conversational and authentic
- NO dashes, NO semicolons
- Use flowing sentences with commas
- End with a question or CTA to drive engagement
- Match this tone if provided: {tone_profile.get('voice_signature', 'conversational, authentic, vulnerable') if tone_profile else 'conversational and authentic'}
"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


DATA_FILE = "data.json"

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"my_posts": [], "drafts": [], "content_links": []}

def save_to_drafts(draft: str) -> None:
    data = load_data()
    drafts = data.get("drafts", [])
    drafts.append(draft)
    data["drafts"] = drafts
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_drafts_list(drafts: List[str]) -> None:
    data = load_data()
    data["drafts"] = drafts
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_all_drafts() -> List[str]:
    data = load_data()
    return data.get("drafts", [])