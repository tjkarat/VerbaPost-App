import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

def record_audio(filename="test_recording.wav", duration=5):
    # 1. Setup configuration
    fs = 44100  # Sample rate (standard CD quality)
    
    print(f"🎙️  Recording for {duration} seconds... Speak now!")
    
    # 2. Start recording
    # This captures raw audio data into the 'myrecording' variable
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    
    # 3. Wait for the recording to finish
    sd.wait()
    
    print("✅ Recording finished.")
    
    # 4. Save as a WAV file
    write(filename, fs, myrecording)
    print(f"💾 Saved to {filename}")

if __name__ == "__main__":
    record_audio()