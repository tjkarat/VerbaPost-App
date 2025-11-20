import whisper
import sys
import re
import os

# Load model once at module level
# We use a try/except block so it doesn't crash if the model download fails temporarily
try:
    model = whisper.load_model("base")
except Exception as e:
    print(f"Model loading error (non-fatal): {e}")
    model = None

def transcribe_audio(filename):
    if model is None:
        return "Error: AI Model not loaded."
        
    print(f"🎧 Transcribing {filename}...")
    result = model.transcribe(filename)
    return result["text"]

def polish_text(text):
    """
    Basic AI Cleanup: Removes filler words.
    """
    fillers = ["um", "uh", "ah", "like, you know", "you know"]
    polished = text
    for filler in fillers:
        pattern = re.compile(re.escape(filler), re.IGNORECASE)
        polished = pattern.sub("", polished)
    
    # Cleanup whitespace
    polished = " ".join(polished.split())
    return polished
