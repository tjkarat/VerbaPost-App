import whisper
import sys

def transcribe_audio(filename="test_recording.wav"):
    print("🧠 Loading the Whisper AI model... (This happens once)")
    # We use the 'base' model. It's a good balance of speed vs accuracy.
    model = whisper.load_model("base")
    
    print(f"🎧 Transcribing '{filename}'...")
    
    # The magic happens here
    result = model.transcribe(filename)
    
    text = result["text"]
    print("\n--- TRANSCRIPTION RESULT ---")
    print(text)
    print("----------------------------")
    
    return text

if __name__ == "__main__":
    # This allows you to run "python3 transcribe.py" to test the default file
    # OR "python3 transcribe.py my_other_file.wav" to test a specific one
    if len(sys.argv) > 1:
        transcribe_audio(sys.argv[1])
    else:
        transcribe_audio()