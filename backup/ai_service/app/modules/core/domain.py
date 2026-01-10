from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field

class SalesSummary(BaseModel):
    """Raw input from the salesman."""
    content: str
    timestamp: Optional[str] = None

class ExtractedEntity(BaseModel):
    """An entity found by the AI model."""
    text: str
    label: str
    score: float

class LeadCandidate(BaseModel):
    """A processed lead ready to be sent to Odoo."""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    source_summary: Optional[str] = None

class EntityExtractor(ABC):
    """Interface for NER extraction."""
    @abstractmethod
    def extract(self, text: str) -> List[ExtractedEntity]:
        pass

class LeadRepository(ABC):
    """Interface for external lead storage/system."""
    @abstractmethod
    def create_lead(self, lead: LeadCandidate) -> int:
        """Creates a lead and returns its external ID."""
        pass
