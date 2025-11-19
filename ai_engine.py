import whisper
import sys
import re

# Load model once at start to save time
# 'tiny' is faster for cloud, 'base' is better accuracy
model = whisper.load_model("base")

def transcribe_audio(filename):
    print(f"🎧 Transcribing {filename}...")
    result = model.transcribe(filename)
    return result["text"]

def polish_text(text):
    """
    Basic AI Cleanup: Removes filler words and fixes basic spacing.
    In the future, we connect this to GPT-4 for full rewriting.
    """
    # Simple cleanup rules
    fillers = ["um", "uh", "ah", "like, you know", "you know"]
    
    polished = text
    for filler in fillers:
        # Case insensitive replace
        pattern = re.compile(re.escape(filler), re.IGNORECASE)
        polished = pattern.sub("", polished)
    
    # Fix double spaces created by removals
    polished = " ".join(polished.split())
    return polished