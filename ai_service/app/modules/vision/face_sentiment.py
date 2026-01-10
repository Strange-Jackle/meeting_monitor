"""
Face Sentiment Analysis Module
30-second screenshot → face detection → sentiment counter

Uses DeepFace for CPU-only emotion detection (Python 3.12 compatible).
"""
import asyncio
import logging
from typing import Callable, Awaitable, Dict, Any

log = logging.getLogger("face_sentiment")


class FaceSentimentAnalyzer:
    """
    Analyzes screenshots for faces and classifies sentiment.
    Uses DeepFace for emotion detection (CPU-only, Python 3.12 compatible).
    """
    
    def __init__(self):
        self._initialized = False
        
    def _lazy_init(self):
        """Lazy initialization to avoid slow startup."""
        if self._initialized:
            return
            
        try:
            from deepface import DeepFace
            log.info("DeepFace available for face sentiment analysis")
            self._initialized = True
        except ImportError as e:
            log.warning(f"DeepFace not installed: {e}. Face sentiment disabled.")
            self._initialized = True
        except Exception as e:
            log.error(f"Failed to initialize DeepFace: {e}")
            self._initialized = True
    
    def _map_emotion_to_binary(self, emotion: str) -> str:
        """Map emotion categories to binary happy/negative."""
        happy_emotions = {"happy", "neutral", "surprise"}
        return "happy" if emotion.lower() in happy_emotions else "negative"
    
    def analyze_screenshot(self, screenshot_array) -> Dict[str, int]:
        """
        Analyze a screenshot for faces and emotions.
        
        Args:
            screenshot_array: numpy array of screenshot (BGRA or RGB format)
            
        Returns:
            {"happy": count, "negative": count}
        """
        self._lazy_init()
        
        try:
            from deepface import DeepFace
            import cv2
            import tempfile
            import os
            
            # Convert BGRA to BGR (OpenCV format) if needed
            if len(screenshot_array.shape) == 3 and screenshot_array.shape[2] == 4:
                img = cv2.cvtColor(screenshot_array, cv2.COLOR_BGRA2BGR)
            else:
                img = screenshot_array
            
            # Save to temp file with unique name (prevents race condition)
            import uuid
            temp_path = os.path.join(tempfile.gettempdir(), f"face_sentiment_{uuid.uuid4().hex}.jpg")
            cv2.imwrite(temp_path, img)
            
            happy_count = 0
            negative_count = 0
            
            try:
                # Analyze with DeepFace (enforce_detection=False to handle no-face cases)
                # Note: This is CPU-intensive (~2-3s), should be run in thread pool
                results = DeepFace.analyze(
                    temp_path, 
                    actions=['emotion'],
                    enforce_detection=False,
                    silent=True,
                    detector_backend='opencv'  # Faster than default 'retinaface'
                )
                
                # Results can be a list or single dict
                if isinstance(results, dict):
                    results = [results]
                
                for face_result in results:
                    if 'dominant_emotion' in face_result:
                        emotion = face_result['dominant_emotion']
                        label = self._map_emotion_to_binary(emotion)
                        
                        if label == "happy":
                            happy_count += 1
                        else:
                            negative_count += 1
                            
                        log.debug(f"Face detected: {emotion} -> {label}")
                        
            except Exception as e:
                # No face detected or analysis failed
                log.debug(f"DeepFace analysis: {e}")
            
            # Cleanup temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            return {"happy": happy_count, "negative": negative_count}
            
        except ImportError:
            log.warning("DeepFace not available")
            return {"happy": 0, "negative": 0}
        except Exception as e:
            log.error(f"Screenshot analysis error: {e}")
            return {"happy": 0, "negative": 0}


# Global analyzer instance
_analyzer = FaceSentimentAnalyzer()


async def face_sentiment_loop(
    session_id: str, 
    broadcast_fn: Callable[[Dict[str, Any]], Awaitable[None]],
    interval: float = 30.0
):
    """
    Async loop that captures screenshots and analyzes face sentiment.
    
    Args:
        session_id: Current session ID
        broadcast_fn: Async callable that broadcasts dict to WebSocket clients
        interval: Seconds between captures (default 30)
    """
    import mss
    import numpy as np
    
    happy_total = 0
    negative_total = 0
    
    log.info(f"[FaceSentiment] Starting loop for session {session_id} (interval: {interval}s)")
    
    with mss.mss() as sct:
        while True:
            try:
                await asyncio.sleep(interval)
                
                # Capture primary monitor
                monitor = sct.monitors[0]  # Primary monitor
                screenshot = sct.grab(monitor)
                img_array = np.array(screenshot)
                
                # Analyze for faces (run in thread pool to prevent blocking event loop)
                # DeepFace is CPU-intensive (~1-3s per call)
                result = await asyncio.to_thread(_analyzer.analyze_screenshot, img_array)
                
                # Accumulate counts
                happy_total += result["happy"]
                negative_total += result["negative"]
                
                # Broadcast to WebSocket
                payload = {
                    "type": "face_sentiment",
                    "happy": happy_total,
                    "negative": negative_total,
                    "session_happy": result["happy"],
                    "session_negative": result["negative"]
                }
                
                log.info(f"[FaceSentiment] Detected {result['happy']} happy, {result['negative']} negative faces (totals: {happy_total}/{negative_total})")
                
                await broadcast_fn(payload)
                
            except asyncio.CancelledError:
                log.info("[FaceSentiment] Loop cancelled")
                break
            except Exception as e:
                log.exception(f"[FaceSentiment] Error in loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry


def analyze_single_screenshot(screenshot_array) -> Dict[str, int]:
    """
    Synchronous single-shot analysis for testing.
    
    Returns:
        {"happy": count, "negative": count}
    """
    return _analyzer.analyze_screenshot(screenshot_array)


if __name__ == "__main__":
    # Standalone test
    import mss
    import numpy as np
    
    logging.basicConfig(level=logging.DEBUG)
    
    print("Capturing screenshot for face sentiment analysis...")
    
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[0])
        img = np.array(screenshot)
        
    result = analyze_single_screenshot(img)
    print(f"Result: {result}")
