import whisper
import sys

# Note: This function is at the "root" level (no indentation)
def transcribe_audio(filename="test_recording.wav"):
    print("🧠 Loading the Whisper AI model...")
    model = whisper.load_model("base")
    
    print(f"🎧 Transcribing {filename}...")
    result = model.transcribe(filename)
    
    text = result["text"]
    print("\n--- TRANSCRIPTION RESULT ---")
    print(text)
    
    return text

if __name__ == "__main__":
    # This block only runs if you execute this file directly
    transcribe_audio()
