import google.generativeai as genai
import os

def list_models():
    api_key = "AIzaSyDk-44dK17_G-RikWFTKcmUamiFLs8QHBY" # user provided key from diff
    if not api_key:
        print("No API Key found.")
        return

    genai.configure(api_key=api_key)
    try:
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
