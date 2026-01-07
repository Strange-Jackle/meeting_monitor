from typing import Dict, Any, List
from app.modules.core.domain import SalesSummary, LeadCandidate, ExtractedEntity
from app.modules.extraction.gliner_service import GLiNERService
from app.modules.odoo_client.client import OdooClient
from app.modules.transcription.service import TranscriptionService
from app.modules.summarization.service import SummarizationService
import shutil
import os

class LeadWorkflowProcessor:
    def __init__(self):
        # In a real app, these would be injected
        self.extractor = GLiNERService()
        self.odoo = OdooClient()
        # Initialize Audio Services
        self.transcriber = TranscriptionService()
        self.summarizer = SummarizationService()

    def process_summary_to_lead(self, summary_content: str) -> Dict[str, Any]:
        """
        Orchestrates: Input -> Extract -> Transform -> Odoo -> Return Result
        """
        # 1. Extraction
        entities: List[ExtractedEntity] = self.extractor.extract(summary_content)
        
        # 2. Transformation / Mapping (Simple Logic)
        candidate = self._map_entities_to_lead(entities, summary_content)
        
        # 3. Create in Odoo
        try:
            lead_id = self.odoo.create_lead(candidate)
            status = "success"
        except Exception as e:
            lead_id = None
            status = f"error: {str(e)}"

        return {
            "status": status,
            "lead_id": lead_id,
            "entities": [e.dict() for e in entities],
            "candidate": candidate.dict()
        }

    def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Orchestrates: Audio -> Transcript -> Summary -> [Process Summary Logic]
        """
        print(f"Processing audio: {file_path}")
        
        # 1. Transcribe
        transcript = self.transcriber.transcribe(file_path)
        print("Transcription complete.")
        
        # 2. Summarize
        summary_text = self.summarizer.summarize(transcript)
        print("Summarization complete.")
        
        # 3. Process the Summary (Reuse existing logic)
        result = self.process_summary_to_lead(summary_text)
        
        # Add intermediate artifacts to result
        result["transcript"] = transcript
        result["summary"] = summary_text
        
        return result

    def _map_entities_to_lead(self, entities: List[ExtractedEntity], original_text: str) -> LeadCandidate:
        candidate = LeadCandidate(
            name="Unknown Lead", # Default
            source_summary=original_text,
            notes="Auto-generated from meeting summary."
        )

        # Naive mapping strategies
        persons = [e.text for e in entities if e.label == 'person']
        emails = [e.text for e in entities if e.label == 'email']
        phones = [e.text for e in entities if e.label == 'phone number']
        orgs = [e.text for e in entities if e.label == 'organization']

        if persons:
            candidate.name = persons[0] 
        if emails:
            candidate.email = emails[0]
        if phones:
            candidate.phone = phones[0]
        if orgs:
            candidate.company = orgs[0]
        
        # If no person found but org found, use org as name
        if candidate.name == "Unknown Lead" and candidate.company:
            candidate.name = f"Contact at {candidate.company}"

        return candidate
