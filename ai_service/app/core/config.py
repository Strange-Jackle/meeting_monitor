from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Load .env file from app directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv()  # Also try current directory

class Settings(BaseSettings):
    PROJECT_NAME: str = "Salesman AI Pro"
    API_V1_STR: str = "/api/v1"
    
    # Hardware Optimization
    DEVICE: str = os.getenv("DEVICE", "cuda")  # cuda or cpu
    COMPUTE_TYPE: str = os.getenv("COMPUTE_TYPE", "float16")  # float16 or int8
    
    # Database
    DATABASE_PATH: str = os.path.join(os.path.dirname(__file__), "..", "..", "meeting_monitor.db")
    
    # Odoo Config
    ODOO_URL: str = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB: str = os.getenv("ODOO_DB", "odoodb")
    ODOO_USER: str = os.getenv("ODOO_USER", "admin")
    ODOO_PASSWORD: str = os.getenv("ODOO_PASSWORD", "admin")
    
    # AI Models
    GLINER_MODEL_NAME: str = "urchade/gliner_small-v2.1"
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "large-v2")  # base/small/medium/large-v2
    SUMMARIZATION_MODEL: str = "knkarthick/MEETING_SUMMARY"
    
    # Gemini Config
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # HuggingFace Token (for pyannote speaker diarization)
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")
    
    # Demo Mode
    DEMO_SIMULATION_MODE: bool = os.getenv("DEMO_SIMULATION_MODE", "false").lower() == "true"

    class Config:
        case_sensitive = True

settings = Settings()
