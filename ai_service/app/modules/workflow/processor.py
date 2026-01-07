from typing import Dict, Any, List
from app.modules.core.domain import SalesSummary, LeadCandidate, ExtractedEntity
from app.modules.extraction.gliner_service import GLiNERService
from app.modules.odoo_client.client import OdooClient
from app.modules.transcription.service import TranscriptionService
from app.modules.summarization.service import SummarizationService
from app.modules.intelligence.gemini_service import GeminiService
from app.modules.intelligence.web_insight_service import WebInsightService # New import
import shutil
import os
import asyncio
import traceback # New import

import nest_asyncio
nest_asyncio.apply()

class LeadWorkflowProcessor:
    def __init__(self):
        # In a real app, these would be injected
        self.extractor = GLiNERService()
        self.odoo = OdooClient()
        # Initialize Audio Services
        self.transcriber = TranscriptionService()
        self.summarizer = SummarizationService()
        # Use Web Insight Service (DuckDuckGo + VADER) - No API Key needed
        self.insights_service = WebInsightService()

    async def process_summary_to_lead(self, summary_content: str) -> Dict[str, Any]:
        """
        Orchestrates: Input -> Extract -> Transform -> Odoo -> Return Result
        """
        print("Processing summary for lead extraction...")
        
        # 1. Extraction
        entities: List[ExtractedEntity] = self.extractor.extract(summary_content)
        print(f"Extracted {len(entities)} entities.")

        # 1.5. Gather Insights (Async/Concurrent)
        insights = []
        tasks = []
        seen_entities = set()

        async def fetch_with_meta(text, label):
             try:
                data = await self.insights_service.get_entity_insights_async(text, label)
                if data:
                    data["entity"] = text
                    data["type"] = label
                return data
             except Exception as e:
                print(f"Error processing insight for {text}: {e}")
                return None

        tasks = []
        seen_entities = set()
        
        # Web Search is free, can handle more concurrency than Gemini Free Tier
        MAX_INSIGHTS = 8
        insights = []

        try:
            print(f"Fetching web insights for top {MAX_INSIGHTS} entities...")

            for e in entities:
                 if len(tasks) >= MAX_INSIGHTS:
                     break

                 if e.label in ["organization", "product", "service"]:
                    key = (e.text, e.label)
                    if key not in seen_entities:
                        seen_entities.add(key)
                        tasks.append(fetch_with_meta(e.text, e.label))
            
            if tasks:
                # Run concurrently for speed
                insights_results = await asyncio.gather(*tasks, return_exceptions=True)
                # Filter out exceptions and Nones
                for r in insights_results:
                    if isinstance(r, Exception):
                        print(f"Insight task failed: {r}")
                    elif r:
                        insights.append(r)
        except Exception as e:
            print(f"CRITICAL ERROR in insight gathering: {e}")
            traceback.print_exc()
            # Continue without insights rather than failing the request
            insights = []
        
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
            "insights": insights,
            "candidate": candidate.dict()
        }

    async def process_audio_file(self, file_path: str) -> Dict[str, Any]:
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
        result = await self.process_summary_to_lead(summary_text)
        
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
