import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import whisper

# Record audio
def record_audio(duration=5, fs=44100):
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='float64')
    sd.wait()  # Wait until recording is finished
    print("Recording stopped.")
    return recording, fs

# Save recording to file
def save_recording(recording, fs, filename='output.wav'):
    write(filename, fs, recording)  # Save as WAV file 

# Transcribe audio with Whisper
def transcribe_audio(filename):
    model = whisper.load_model("base")  # Load Whisper model
    result = model.transcribe(filename)
    print("Transcription: ", result['text'])

if __name__ == "__main__":
    duration = 5  # Duration of the recording in seconds
    fs = 44100  # Sample rate
    
    # Record and save audio
    recording, fs = record_audio(duration, fs)
    filename = 'output.wav'
    save_recording(recording, fs, filename)
    
    # Transcribe the saved audio file
    transcribe_audio(filename)
