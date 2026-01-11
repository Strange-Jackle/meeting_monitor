"""
WhisperX Transcription Service with Speaker Diarization.

Features:
- GPU-accelerated transcription (large-v2 model)
- Speaker diarization via pyannote.audio
- Word-level timestamps with speaker alignment
- Graceful fallback to CPU if CUDA fails
"""

import os
import torch
from typing import List, Dict, Optional, Any
from app.core.config import settings


class TranscriptionService:
    """GPU-accelerated transcription with speaker diarization."""
    
    def __init__(self):
        self.device = settings.DEVICE if torch.cuda.is_available() else "cpu"
        self.compute_type = settings.COMPUTE_TYPE if self.device == "cuda" else "int8"
        self.model = None
        self.diarize_model = None
        self.hf_token = settings.HF_TOKEN
        
        self.hf_token = settings.HF_TOKEN
        
        # Ensure FFmpeg is available
        self._ensure_ffmpeg()
        
        # Load model on init
        self._load_model()

    def _ensure_ffmpeg(self):
        """Check for FFmpeg and add to PATH if necessary."""
        import shutil
        import os
        
        if shutil.which("ffmpeg"):
            print("[System] FFmpeg found in PATH")
            return

        print("[System] FFmpeg not found in PATH. Checking common locations...")
        
        # Common Windows locations for Winget/Chocolatey/Manual installs
        possible_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-essentials_build\bin"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links"),
            r"C:\ProgramData\chocolatey\bin",
            r"C:\ffmpeg\bin",
        ]
        
        # Search recursively in LocalAppData for ffmpeg.exe if standard paths fail
        # (Winget paths change with version numbers)
        if not any(os.path.exists(p) for p in possible_paths):
            print("[System] Searching deeply for ffmpeg.exe...")
            base_search = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
            if os.path.exists(base_search):
                for root, dirs, files in os.walk(base_search):
                    if "ffmpeg.exe" in files:
                        possible_paths.append(root)
                        break

        found = False
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "ffmpeg.exe")):
                print(f"[System] Found FFmpeg at: {path}")
                os.environ["PATH"] += os.pathsep + path
                found = True
                break
        
        if not found:
            print("[System] WARNING: FFmpeg not found! Transcription will likely fail.")
            print("Please run: winget install 'FFmpeg (Essentials Build)'")
    
    def _load_model(self):
        """Load WhisperX model."""
        try:
            import whisperx
            
            print(f"[WhisperX] Loading {settings.WHISPER_MODEL_SIZE} on {self.device.upper()} ({self.compute_type})...")
            
            self.model = whisperx.load_model(
                settings.WHISPER_MODEL_SIZE,
                device=self.device,
                compute_type=self.compute_type
            )
            
            print(f"[WhisperX] Model loaded successfully!")
            
            # Load diarization model if HF token available
            if self.hf_token:
                try:

                    print("[WhisperX] Loading speaker diarization pipeline...")
                    from whisperx.diarize import DiarizationPipeline
                    self.diarize_model = DiarizationPipeline(
                        use_auth_token=self.hf_token,
                        device=self.device
                    )
                    print("[WhisperX] Diarization pipeline ready!")
                except Exception as e:
                    print(f"[WhisperX] Warning: Diarization unavailable: {e}")
                    if "401" in str(e) or "403" in str(e) or "gated" in str(e).lower():
                         print("="*60)
                         print("ACTION REQUIRED: You must accept terms for these 2 models:")
                         print("1. https://huggingface.co/pyannote/speaker-diarization-3.1")
                         print("2. https://huggingface.co/pyannote/segmentation-3.0")
                         print("Then create a Read token at https://huggingface.co/settings/tokens")
                         print("And add it to your .env file as HF_TOKEN=...")
                         print("="*60)
                    self.diarize_model = None
            else:
                print("[WhisperX] Warning: No HF_TOKEN - speaker diarization disabled")
                
        except Exception as e:
            print(f"[WhisperX] CRITICAL: Failed to load on {self.device}: {e}")
            
            if self.device == "cuda":
                print("[WhisperX] Falling back to CPU...")
                self.device = "cpu"
                self.compute_type = "int8"
                self._load_model()
            else:
                raise RuntimeError(f"WhisperX failed to load: {e}")
    
    def transcribe(self, file_path: str) -> str:
        """
        Basic transcription - returns plain text.
        For backwards compatibility with existing code.
        """
        result = self.transcribe_with_speakers(file_path)
        
        if not result:
            return ""
        
        # Combine all segments into plain text
        texts = [seg.get("text", "") for seg in result]
        return " ".join(texts).strip()
    
    def transcribe_with_speakers(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe audio with speaker diarization.
        
        Returns:
            List of segments with speaker, text, and timestamp:
            [
                {"speaker": "SPEAKER_00", "text": "Hello there", "start": 0.0, "end": 1.5},
                {"speaker": "SPEAKER_01", "text": "Hi, how are you?", "start": 1.8, "end": 3.2},
            ]
        """
        if not os.path.exists(file_path):
            print(f"[WhisperX] Warning: File not found: {file_path}")
            return []
        
        if not self.model:
            print("[WhisperX] Error: Model not loaded")
            return []
        
        try:
            import whisperx
            
            # Step 1: Transcribe
            audio = whisperx.load_audio(file_path)
            result = self.model.transcribe(audio, batch_size=16)
            
            language = result.get("language", "en")
            print(f"[WhisperX] Detected language: {language}")
            
            # Step 2: Align timestamps (word-level)
            try:
                model_a, metadata = whisperx.load_align_model(
                    language_code=language, 
                    device=self.device
                )
                result = whisperx.align(
                    result["segments"], 
                    model_a, 
                    metadata, 
                    audio, 
                    self.device,
                    return_char_alignments=False
                )
            except Exception as e:
                print(f"[WhisperX] Alignment warning: {e}")
            
            # Step 3: Diarization (if available)
            if self.diarize_model and audio is not None:
                try:
                    diarize_segments = self.diarize_model(audio)
                    result = whisperx.assign_word_speakers(diarize_segments, result)
                except Exception as e:
                    print(f"[WhisperX] Diarization warning: {e}")
            
            # Step 4: Format output
            segments = result.get("segments", [])
            output = []
            
            for seg in segments:
                output.append({
                    "speaker": seg.get("speaker", "SPEAKER_00"),
                    "text": seg.get("text", "").strip(),
                    "start": seg.get("start", 0.0),
                    "end": seg.get("end", 0.0)
                })
            
            return output
            
        except Exception as e:
            print(f"[WhisperX] Transcription error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def format_transcript_with_speakers(self, segments: List[Dict[str, Any]]) -> str:
        """Format diarized segments into readable transcript."""
        if not segments:
            return ""
        
        lines = []
        current_speaker = None
        current_text = []
        
        for seg in segments:
            speaker = seg.get("speaker", "SPEAKER_00")
            text = seg.get("text", "").strip()
            
            if speaker != current_speaker:
                if current_text:
                    lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
                current_speaker = speaker
                current_text = [text] if text else []
            else:
                if text:
                    current_text.append(text)
        
        # Add last speaker's text
        if current_text:
            lines.append(f"[{current_speaker}]: {' '.join(current_text)}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    print("Testing WhisperX Transcription Service...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"Device: {settings.DEVICE}")
    print(f"Model: {settings.WHISPER_MODEL_SIZE}")
    
    # service = TranscriptionService()
    # result = service.transcribe_with_speakers("test.wav")
    # print(service.format_transcript_with_speakers(result))
