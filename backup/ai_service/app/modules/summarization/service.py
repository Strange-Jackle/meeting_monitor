from transformers import pipeline
from app.core.config import settings
import torch

class SummarizationService:
    def __init__(self):
        # Use GPU if available, fallback to CPU
        device = 0 if torch.cuda.is_available() else -1
        device_name = "GPU" if device == 0 else "CPU"
        
        print(f"Loading Summarization model: {settings.SUMMARIZATION_MODEL} on {device_name}...")
        self.summarizer = pipeline("summarization", model=settings.SUMMARIZATION_MODEL, device=device)
        print(f"Summarization model loaded on {device_name}.")

    def summarize(self, text: str) -> str:
        # BART has a limit of 1024 tokens. We should ideally chunk long text.
        # For this MVP, we will truncate if too long, or rely on pipeline's truncation.
        # min_length=50, max_length=150 is typical for a summary
        
        # Calculate dynamic max_length based on input? Or fixed?
        # Let's use a reasonable default for meeting minutes.
        try:
            summary_output = self.summarizer(text, max_length=500, min_length=50, do_sample=False, truncation=True)
            return summary_output[0]['summary_text']
        except Exception as e:
            print(f"Summarization error: {e}")
            return text # Fallback to original text on failure

if __name__ == "__main__":
    print("Running Summarization Test...")
    service = SummarizationService()
    text = "Detailed meeting transcript goes here..." * 50
    print(service.summarize(text))
