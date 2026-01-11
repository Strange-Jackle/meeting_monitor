"""
Local Capture Service - Screen and Audio capture for Stealth Assistant.

Captures:
1. Screen: Using mss for fast screenshot capture (2s intervals)
2. Audio: Using sounddevice with WASAPI loopback for system audio capture
"""

import asyncio
import queue
import threading
import time
import io
import wave
import tempfile
import os
from dataclasses import dataclass, field
from typing import Optional, Callable, List
from PIL import Image
import numpy as np
import base64

# Screen capture
import mss
import mss.tools

# Audio capture
import sounddevice as sd
import soundfile as sf


@dataclass
class CaptureConfig:
    """Configuration for capture services."""
    # Screen capture settings
    screen_interval: float = 2.0  # seconds between screenshots
    screen_region: Optional[dict] = None  # None = full primary monitor
    
    # Audio capture settings
    audio_chunk_duration: float = 10.0  # seconds per audio chunk
    audio_sample_rate: int = 16000  # Whisper prefers 16kHz
    audio_channels: int = 1  # Mono for transcription
    
    # Processing settings
    max_queue_size: int = 10


@dataclass
class AudioChunk:
    """Represents a captured audio segment."""
    data: np.ndarray
    sample_rate: int
    timestamp: float
    duration: float


@dataclass
class Screenshot:
    """Represents a captured screenshot."""
    image: Image.Image
    timestamp: float
    

class LocalCaptureService:
    """
    Async service for capturing screen and audio.
    Designed to run concurrently without blocking the main event loop.
    """
    
    def __init__(self, config: Optional[CaptureConfig] = None):
        self.config = config or CaptureConfig()
        
        # State
        self._running = False
        self._screen_task: Optional[asyncio.Task] = None
        self._audio_thread: Optional[threading.Thread] = None
        
        # Queues for captured data
        self._screenshot_queue: queue.Queue = queue.Queue(maxsize=self.config.max_queue_size)
        self._audio_queue: queue.Queue = queue.Queue(maxsize=self.config.max_queue_size)
        
        # Latest captures (for real-time access)
        self._latest_screenshot: Optional[Screenshot] = None
        self._latest_audio_chunk: Optional[AudioChunk] = None
        
        # Callbacks
        self._on_screenshot: Optional[Callable[[Screenshot], None]] = None
        self._on_audio_chunk: Optional[Callable[[AudioChunk], None]] = None
        
        # Audio stream
        self._audio_stream = None
        self._audio_buffer: List[np.ndarray] = []
        self._audio_buffer_start_time: float = 0
        
        print("[LocalCapture] Service initialized")
    
    def set_callbacks(
        self,
        on_screenshot: Optional[Callable[[Screenshot], None]] = None,
        on_audio_chunk: Optional[Callable[[AudioChunk], None]] = None
    ):
        """Set callbacks for real-time data."""
        self._on_screenshot = on_screenshot
        self._on_audio_chunk = on_audio_chunk
    
    async def start(self):
        """Start all capture loops."""
        if self._running:
            print("[LocalCapture] Already running")
            return
        
        self._running = True
        
        # Check for demo simulation mode
        from app.core.config import settings
        if settings.DEMO_SIMULATION_MODE:
            print("[LocalCapture] *** DEMO SIMULATION MODE ACTIVE ***")
            self._demo_thread = threading.Thread(target=self._demo_simulation_loop, daemon=True)
            self._demo_thread.start()
            return
        
        print("[LocalCapture] Starting capture loops...")
        
        # Start screen capture (async)
        self._screen_task = asyncio.create_task(self._screen_capture_loop())
        
        # Start audio capture (threaded - sounddevice is blocking)
        self._audio_thread = threading.Thread(target=self._audio_capture_loop, daemon=True)
        self._audio_thread.start()
        
        print("[LocalCapture] Capture loops started")
    
    async def stop(self):
        """Stop all capture loops."""
        if not self._running:
            return
        
        self._running = False
        print("[LocalCapture] Stopping capture loops...")
        
        # Stop screen capture
        if self._screen_task:
            self._screen_task.cancel()
            try:
                await self._screen_task
            except asyncio.CancelledError:
                pass
        
        # Stop audio stream
        if self._audio_stream:
            self._audio_stream.stop()
            self._audio_stream.close()
            self._audio_stream = None
        
        # Force stop any remaining sounddevice streams
        try:
            import sounddevice as sd
            sd.stop()
        except:
            pass
        
        # Wait for audio thread
        if self._audio_thread and self._audio_thread.is_alive():
            self._audio_thread.join(timeout=2.0)
        
        # Clear queues
        while not self._screenshot_queue.empty():
            try:
                self._screenshot_queue.get_nowait()
            except:
                break
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except:
                break
        
        print("[LocalCapture] Capture loops stopped")
    
    # ==================== SCREEN CAPTURE ====================
    
    async def _screen_capture_loop(self):
        """Async loop for screen capture."""
        print(f"[LocalCapture] Screen capture loop started (interval: {self.config.screen_interval}s)")
        
        with mss.mss() as sct:
            # Determine capture region
            if self.config.screen_region:
                monitor = self.config.screen_region
            else:
                # Primary monitor (index 1, index 0 is "all monitors")
                monitor = sct.monitors[1]
            
            while self._running:
                try:
                    # Capture screenshot
                    screenshot = sct.grab(monitor)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    
                    # Create Screenshot object
                    capture = Screenshot(image=img, timestamp=time.time())
                    
                    # Update latest
                    self._latest_screenshot = capture
                    
                    # Add to queue (non-blocking)
                    try:
                        self._screenshot_queue.put_nowait(capture)
                    except queue.Full:
                        # Remove oldest and add new
                        try:
                            self._screenshot_queue.get_nowait()
                            self._screenshot_queue.put_nowait(capture)
                        except queue.Empty:
                            pass
                    
                    # Call callback if set
                    if self._on_screenshot:
                        self._on_screenshot(capture)
                    
                    # Wait for next interval
                    await asyncio.sleep(self.config.screen_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"[LocalCapture] Screen capture error: {e}")
                    await asyncio.sleep(1.0)
        
        print("[LocalCapture] Screen capture loop ended")
    
    # ==================== AUDIO CAPTURE ====================
    
    def _get_loopback_device(self) -> tuple:
        """
        Find WASAPI loopback device for system audio capture.
        Returns: (device_id, native_sample_rate)
        """
        try:
            devices = sd.query_devices()
            
            # Priority 1: Look for Stereo Mix / loopback devices
            for i, device in enumerate(devices):
                name = device['name'].lower()
                
                # Stereo Mix is the best for system audio
                if 'stereo mix' in name and device['max_input_channels'] > 0:
                    native_rate = int(device['default_samplerate'])
                    print(f"[LocalCapture] Found Stereo Mix: {device['name']} (index {i}, {native_rate}Hz)")
                    return (i, native_rate)
            
            # Priority 2: WASAPI loopback patterns
            for i, device in enumerate(devices):
                name = device['name'].lower()
                hostapi = sd.query_hostapis(device['hostapi'])['name'].lower()
                
                if 'wasapi' in hostapi and device['max_input_channels'] > 0:
                    if 'loopback' in name or 'what u hear' in name:
                        native_rate = int(device['default_samplerate'])
                        print(f"[LocalCapture] Found loopback device: {device['name']} (index {i}, {native_rate}Hz)")
                        return (i, native_rate)
            
            # Priority 3: Any WDM-KS Stereo Mix
            for i, device in enumerate(devices):
                name = device['name'].lower()
                if 'stereo mix' in name and device['max_input_channels'] > 0:
                    native_rate = int(device['default_samplerate'])
                    print(f"[LocalCapture] Found WDM Stereo Mix: {device['name']} (index {i}, {native_rate}Hz)")
                    return (i, native_rate)
            
            # Fallback: Default input device with its native rate
            default_device = sd.query_devices(kind='input')
            native_rate = int(default_device['default_samplerate'])
            print(f"[LocalCapture] Using default input: {default_device['name']} ({native_rate}Hz)")
            return (None, native_rate)
            
        except Exception as e:
            print(f"[LocalCapture] Error finding loopback device: {e}")
            return (None, 44100)  # Safe fallback
    
    def _audio_capture_loop(self):
        """Threaded loop for audio capture using WASAPI."""
        print(f"[LocalCapture] Audio capture loop started (chunk duration: {self.config.audio_chunk_duration}s)")
        
        while self._running:
            try:
                # Find loopback device and its native sample rate
                device_id, native_rate = self._get_loopback_device()
                
                # Store the actual sample rate we're using
                self._actual_sample_rate = native_rate
                
                # Reset buffer on start
                self._audio_buffer = []
                self._audio_buffer_start_time = time.time()
                
                def audio_callback(indata, frames, time_info, status):
                    """Called by sounddevice for each audio block."""
                    if status:
                        print(f"[LocalCapture] Audio status: {status}")
                    
                    # Copy data to buffer
                    self._audio_buffer.append(indata.copy())
                    
                    # Check if we have enough for a chunk (using actual sample rate)
                    total_samples = sum(len(chunk) for chunk in self._audio_buffer)
                    chunk_samples = int(self.config.audio_chunk_duration * self._actual_sample_rate)
                    
                    if total_samples >= chunk_samples:
                        self._process_audio_buffer()
                
                # Open stream with DEVICE'S native sample rate (not forced 16kHz)
                print(f"[LocalCapture] Opening audio stream at {native_rate}Hz...")
                self._audio_stream = sd.InputStream(
                    device=device_id,
                    samplerate=native_rate,  # Use device's native rate
                    channels=self.config.audio_channels,
                    dtype=np.float32,
                    callback=audio_callback,
                    blocksize=1024
                )
                self._audio_stream.start()
                print(f"[LocalCapture] Audio stream started successfully!")
                
                # Keep thread alive while running and stream is active
                while self._running and self._audio_stream.active:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"[LocalCapture] Audio capture error (restarting in 2s): {e}")
                import traceback
                traceback.print_exc()
                time.sleep(2.0)
            
            finally:
                if self._audio_stream:
                    try:
                        self._audio_stream.stop()
                        self._audio_stream.close()
                    except:
                        pass
                    self._audio_stream = None

        print("[LocalCapture] Audio capture loop ended")
    
    def _process_audio_buffer(self):
        """Process accumulated audio buffer into a chunk."""
        if not self._audio_buffer:
            return
        
        # Get actual sample rate (may differ from config if device doesn't support it)
        sample_rate = getattr(self, '_actual_sample_rate', self.config.audio_sample_rate)
        
        # Concatenate all audio data
        audio_data = np.concatenate(self._audio_buffer, axis=0)
        
        # Create AudioChunk
        duration = len(audio_data) / sample_rate
        chunk = AudioChunk(
            data=audio_data,
            sample_rate=sample_rate,
            timestamp=self._audio_buffer_start_time,
            duration=duration
        )
        
        # Update latest
        self._latest_audio_chunk = chunk
        
        # Add to queue
        try:
            self._audio_queue.put_nowait(chunk)
        except queue.Full:
            try:
                self._audio_queue.get_nowait()
                self._audio_queue.put_nowait(chunk)
            except queue.Empty:
                pass
        
        # Call callback
        if self._on_audio_chunk:
            self._on_audio_chunk(chunk)
        
        # Reset buffer
        self._audio_buffer = []
        self._audio_buffer_start_time = time.time()
    
    # ==================== DATA ACCESS ====================
    
    def get_latest_screenshot(self) -> Optional[Screenshot]:
        """Get the most recent screenshot."""
        return self._latest_screenshot
    
    def get_latest_audio_chunk(self) -> Optional[AudioChunk]:
        """Get the most recent audio chunk."""
        return self._latest_audio_chunk
    
    def get_screenshot_queue(self) -> queue.Queue:
        """Get the screenshot queue for external processing."""
        return self._screenshot_queue
    
    def get_audio_queue(self) -> queue.Queue:
        """Get the audio queue for external processing."""
        return self._audio_queue
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    # ==================== UTILITY METHODS ====================
    
    @staticmethod
    def screenshot_to_base64(screenshot: Screenshot, format: str = "JPEG", quality: int = 85) -> str:
        """Convert a screenshot to base64 string for API transmission."""
        buffer = io.BytesIO()
        screenshot.image.save(buffer, format=format, quality=quality)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    @staticmethod
    def audio_chunk_to_wav_file(chunk: AudioChunk) -> str:
        """Save an audio chunk to a temporary WAV file for Whisper."""
        # Create temp file
        fd, filepath = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        # Write WAV
        sf.write(filepath, chunk.data, chunk.sample_rate)
        
        return filepath
    
    def _demo_simulation_loop(self):
        """
        Demo simulation mode - replays transcript at realistic pace.
        Used for reliable hackathon demos when live audio might fail.
        """
        import os
        
        # Find demo transcript file
        demo_file = os.path.join(
            os.path.dirname(__file__), 
            "..", "..", "..", "demo_transcript.txt"
        )
        
        if not os.path.exists(demo_file):
            print(f"[Demo] Warning: Demo transcript not found at {demo_file}")
            demo_file = os.path.join(os.path.dirname(__file__), "..", "..", "demo_transcript.txt")
        
        if not os.path.exists(demo_file):
            print("[Demo] Error: No demo transcript file found!")
            return
        
        # Read transcript
        with open(demo_file, "r", encoding="utf-8") as f:
            transcript_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"[Demo] Loaded {len(transcript_lines)} lines for simulation")
        
        # Simulate at realistic pace (one line every 5-10 seconds)
        import random
        
        chunk_size = 3  # Combine 3 lines per "chunk"
        line_index = 0
        
        while self._running and line_index < len(transcript_lines):
            # Combine several lines into one chunk
            chunk_lines = transcript_lines[line_index:line_index + chunk_size]
            chunk_text = " ".join(chunk_lines)
            line_index += chunk_size
            
            # Parse speaker from text (format: "Speaker: text")
            speaker = "SPEAKER_00"
            text = chunk_text
            if ": " in chunk_text:
                parts = chunk_text.split(": ", 1)
                speaker_raw = parts[0].strip().upper().replace(" ", "_")
                if "SALES" in speaker_raw or "REP" in speaker_raw:
                    speaker = "SALES_REP"
                elif "CLIENT" in speaker_raw:
                    speaker = "CLIENT"
                else:
                    speaker = speaker_raw[:15]  # Truncate long names
                text = parts[1] if len(parts) > 1 else chunk_text
            
            # Create fake audio chunk with silence (just for the callback structure)
            # The actual text comes from the transcript file
            fake_audio = np.zeros(int(self.config.audio_sample_rate * self.config.audio_chunk_duration), dtype=np.float32)
            
            chunk = AudioChunk(
                data=fake_audio + np.random.randn(len(fake_audio)) * 0.001,  # Tiny noise so not detected as silent
                sample_rate=self.config.audio_sample_rate,
                timestamp=time.time(),
                duration=self.config.audio_chunk_duration
            )
            
            # Store the simulated text in the chunk metadata by using a special attribute
            chunk._demo_text = text
            chunk._demo_speaker = speaker
            
            # Call the audio callback
            if self._on_audio_chunk:
                print(f"[Demo] Simulating: [{speaker}] {text[:40]}...")
                self._on_audio_chunk(chunk)
            
            # Wait realistic time (6-10 seconds)
            wait_time = random.uniform(6.0, 10.0)
            for _ in range(int(wait_time * 10)):  # Check running every 0.1s
                if not self._running:
                    break
                time.sleep(0.1)
        
        print("[Demo] Simulation complete!")


# ==================== TEST FUNCTIONS ====================

async def test_screen_capture():
    """Test screen capture functionality."""
    print("Testing screen capture...")
    
    service = LocalCaptureService()
    
    screenshots = []
    def on_screenshot(ss):
        screenshots.append(ss)
        print(f"  Captured screenshot at {ss.timestamp:.2f} ({ss.image.size})")
    
    service.set_callbacks(on_screenshot=on_screenshot)
    
    await service.start()
    await asyncio.sleep(5)  # Capture for 5 seconds
    await service.stop()
    
    print(f"Captured {len(screenshots)} screenshots")
    if screenshots:
        # Save last screenshot
        screenshots[-1].image.save("test_screenshot.png")
        print("Saved test_screenshot.png")


def test_audio_devices():
    """List available audio devices."""
    print("Available audio devices:")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        hostapi = sd.query_hostapis(d['hostapi'])['name']
        in_ch = d['max_input_channels']
        out_ch = d['max_output_channels']
        print(f"  [{i}] {d['name']} ({hostapi}) - In: {in_ch}, Out: {out_ch}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-screen":
            asyncio.run(test_screen_capture())
        elif sys.argv[1] == "--test-audio":
            test_audio_devices()
        else:
            print("Usage: python local_capture.py [--test-screen | --test-audio]")
    else:
        print("Local Capture Service")
        print("Run with --test-screen or --test-audio to test functionality")
        test_audio_devices()
