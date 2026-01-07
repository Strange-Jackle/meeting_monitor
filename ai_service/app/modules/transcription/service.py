from faster_whisper import WhisperModel
from app.core.config import settings
import os

class TranscriptionService:
    def __init__(self):
        print(f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE} ...")
        # Run on CPU with INT8 quantization for speed
        self.model = WhisperModel(settings.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        print("Whisper model loaded.")

    def transcribe(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        segments, info = self.model.transcribe(file_path, beam_size=5)
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")

        transcript = []
        for segment in segments:
            transcript.append(segment.text)
            
        full_text = " ".join(transcript)
        return full_text.strip()

if __name__ == "__main__":
    # Standalone Test
    print("Running Transcription Test...")
    # Requires a sample.wav in the current folder or path
    # service = TranscriptionService()
    # print(service.transcribe("sample.wav"))
