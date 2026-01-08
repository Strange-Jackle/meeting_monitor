from faster_whisper import WhisperModel
from app.core.config import settings
import os
import torch

class TranscriptionService:
    def __init__(self):
        # Detect GPU availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE} on {device.upper()}...")
        self.model = WhisperModel(settings.WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)
        print(f"Whisper model loaded on {device.upper()} with {compute_type} precision.")

    def transcribe(self, file_path: str) -> str:
        """Transcribe an audio file to text."""
        if not os.path.exists(file_path):
            print(f"[Transcription] Warning: Audio file not found: {file_path}")
            return ""  # Return empty instead of crashing
        
        try:
            segments, info = self.model.transcribe(file_path, beam_size=5)
            
            print(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")

            transcript = []
            for segment in segments:
                transcript.append(segment.text)
                
            full_text = " ".join(transcript)
            return full_text.strip()
            
        except Exception as e:
            print(f"[Transcription] Error transcribing audio: {e}")
            return ""  # Return empty on error

if __name__ == "__main__":
    # Standalone Test
    print("Running Transcription Test...")
    # Requires a sample.wav in the current folder or path
    # service = TranscriptionService()
    # print(service.transcribe("sample.wav"))
