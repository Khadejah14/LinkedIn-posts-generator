"""Voice to Draft feature - transcribe audio, clean, and structure into LinkedIn posts."""

import re
from llm import LLM
from config import STRUCTURE_DRAFT_PROMPT, GENERATE_POST_PROMPT, FILLER_WORDS, MAX_FILE_SIZE
from utils import load_data, save_data


def clean_transcript(text: str) -> str:
    """Clean filler words and fix run-on sentences."""
    text = text.lower()
    for pattern in FILLER_WORDS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(s)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\.+", ".", text)
    text = re.sub(r",+", ",", text)
    text = re.sub(r"\s+([.,!?])", r"\1", text)
    text = re.sub(r"([.,!?])\s+([.,!?])", r"\1\2", text)
    return text.strip()


def split_audio(audio_data: bytes) -> list[bytes]:
    """Split audio if over 25MB."""
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


def transcribe(audio_data: bytes, filename: str = "audio.mp3") -> str:
    """Transcribe audio via Whisper."""
    parts = split_audio(audio_data)
    llm = LLM()
    
    if len(parts) > 1:
        transcripts = []
        for part in parts:
            transcripts.append(llm.transcribe(part, f"part_{filename}"))
        return " ".join(transcripts)
    return llm.transcribe(audio_data, filename)


def structure(text: str) -> dict[str, str]:
    """Structure transcript into hook/body/CTA."""
    llm = LLM()
    prompt = STRUCTURE_DRAFT_PROMPT.format(text=text)
    return llm.chat(prompt, json_mode=True)


def generate_post(draft: str, tone: str = None) -> str:
    """Generate polished LinkedIn post from draft."""
    llm = LLM()
    prompt = GENERATE_POST_PROMPT.format(draft=draft, tone=tone or "conversational and authentic")
    return llm.chat_text(prompt)


def add_to_drafts(text: str) -> None:
    """Save draft to data.json."""
    data = load_data()
    data.setdefault("drafts", []).append(text)
    save_data(data)


def get_drafts() -> list[str]:
    """Get all drafts from data.json."""
    return load_data().get("drafts", [])