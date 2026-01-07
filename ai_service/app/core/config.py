from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Salesman AI Service"
    API_V1_STR: str = "/api/v1"
    
    # Odoo Config
    ODOO_URL: str = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB: str = os.getenv("ODOO_DB", "odoodb")
    ODOO_USER: str = os.getenv("ODOO_USER", "admin")
    ODOO_PASSWORD: str = os.getenv("ODOO_PASSWORD", "admin")
    
    # AI Config
    GLINER_MODEL_NAME: str = "urchade/gliner_small-v2.1"
    WHISPER_MODEL_SIZE: str = "medium" # or "small", "base"
    SUMMARIZATION_MODEL: str = "knkarthick/MEETING_SUMMARY"

    class Config:
        case_sensitive = True

settings = Settings()
