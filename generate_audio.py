from gtts import gTTS
import os

def generate_audio():
    # Read a portion of the transcript to keep it reasonably short for testing
    try:
        with open("long_meeting_transcript.txt", "r", encoding="utf-8") as f:
            text = f.read()
            # Take the first 2000 characters to ensure we capture some entities
            # but don't spend forever generating audio
            if len(text) > 2000:
                text = text[:2000]
    except FileNotFoundError:
        print("Transcript file not found, using default text.")
        text = "This is a meeting about Microsoft Azure and Slack integration."

    print(f"Generating audio for {len(text)} characters...")
    tts = gTTS(text, lang='en')
    output_file = "sample_long_meeting.mp3"
    tts.save(output_file)
    print(f"Audio saved to {output_file}")

if __name__ == "__main__":
    generate_audio()
