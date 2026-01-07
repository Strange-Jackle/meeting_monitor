from fastapi import APIRouter, HTTPException, UploadFile, File
from app.modules.core.domain import SalesSummary
from app.modules.workflow.processor import LeadWorkflowProcessor
import shutil
import os
import uuid

router = APIRouter()
processor = LeadWorkflowProcessor() # Singleton-ish context

@router.post("/process-summary")
async def process_summary(summary: SalesSummary):
    try:
        result = processor.process_summary_to_lead(summary.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-audio")
async def process_audio(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    temp_path = os.path.join("temp_audio", temp_filename)
    
    # Ensure temp dir exists
    os.makedirs("temp_audio", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        result = processor.process_audio_file(temp_path)
        return result
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
