from typing import List, Dict, Optional
from gliner import GLiNER
from app.modules.core.domain import EntityExtractor, ExtractedEntity
from app.core.config import settings
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random


class GLiNERService(EntityExtractor):
    """
    Extended GLiNER service for entity extraction, hint generation, and battlecards.
    Replaces Gemini for text-based analysis tasks.
    """
    
    def __init__(self):
        print(f"Loading GLiNER model: {settings.GLINER_MODEL_NAME}...")
        self.model = GLiNER.from_pretrained(settings.GLINER_MODEL_NAME)
        self.labels = ["person", "email", "phone number", "organization", "location", "date", "product", "service"]
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        print("GLiNER model loaded.")
        
        # Rule-based hint templates by entity type
        self.HINT_TEMPLATES = {
            "organization": [
                "Research {entity} before follow-up",
                "Ask about {entity} relationship",
                "Mention our {entity} partnership",
                "Compare pricing with {entity}"
            ],
            "product": [
                "Highlight our {entity} alternative",
                "Ask about {entity} satisfaction",
                "Compare features vs {entity}",
                "Mention {entity} limitations"
            ],
            "service": [
                "Ask about {entity} experience",
                "Offer our {entity} equivalent",
                "Discuss {entity} pricing concerns",
                "Highlight {entity} gaps we fill"
            ],
            "person": [
                "Connect with {entity} post-call",
                "Note {entity}'s key concerns",
                "Follow up with {entity} directly",
                "Send {entity} case study"
            ]
        }
        
        # Generic hints for when no entities detected
        self.GENERIC_HINTS = [
            "Ask about their timeline",
            "Discuss budget range",
            "Identify decision makers",
            "Ask about current solution",
            "Mention customer success stories",
            "Offer product demo",
            "Discuss implementation process",
            "Ask about team size"
        ]
        
        # Competitor battlecard templates
        self.BATTLECARD_DB = {
            "aws": {
                "counter_points": [
                    "Simpler pricing - no hidden fees",
                    "24/7 dedicated support vs ticket system",
                    "Faster onboarding - 2 weeks vs 2 months"
                ],
                "quick_response": "AWS is powerful, but we offer better ROI and support for mid-market."
            },
            "salesforce": {
                "counter_points": [
                    "50% lower total cost of ownership",
                    "Modern, intuitive UI - minimal training",
                    "No vendor lock-in - open APIs"
                ],
                "quick_response": "Salesforce is enterprise-heavy. We're built for agile teams like yours."
            },
            "datadog": {
                "counter_points": [
                    "Predictable pricing - no surprise bills",
                    "Same observability at 40% less cost",
                    "No per-host pricing gotchas"
                ],
                "quick_response": "Datadog is great, but our transparent pricing means no 'Datadolla' surprises."
            },
            "microsoft": {
                "counter_points": [
                    "Better UX - 60% faster adoption",
                    "No Office 365 bundle required",
                    "Superior integrations with modern tools"
                ],
                "quick_response": "We integrate where Microsoft bundles. More flexibility for your stack."
            },
            "hubspot": {
                "counter_points": [
                    "More advanced automation features",
                    "Better reporting and analytics",
                    "Scales without enterprise pricing jump"
                ],
                "quick_response": "HubSpot is great to start, but we scale better as you grow."
            },
            "slack": {
                "counter_points": [
                    "Better enterprise security controls",
                    "Lower per-seat pricing at scale",
                    "Native CRM integration"
                ],
                "quick_response": "Slack is popular, but we offer deeper business tool integration."
            }
        }

    def extract(self, text: str) -> List[ExtractedEntity]:
        """Extract entities from text using GLiNER."""
        entities = self.model.predict_entities(text, self.labels)
        
        extracted = []
        for e in entities:
            extracted.append(ExtractedEntity(
                text=e["text"],
                label=e["label"],
                score=e["score"]
            ))
        return extracted
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using VADER."""
        scores = self.sentiment_analyzer.polarity_scores(text)
        
        if scores['compound'] >= 0.05:
            sentiment = "positive"
        elif scores['compound'] <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        return {
            "sentiment": sentiment,
            "compound": scores['compound'],
            "positive": scores['pos'],
            "negative": scores['neg'],
            "neutral": scores['neu']
        }
    
    def generate_hints(
        self, 
        entities: List[ExtractedEntity], 
        transcript: str = "",
        max_hints: int = 3
    ) -> Dict:
        """
        Generate sales hints based on extracted entities.
        
        Returns:
            {
                "quick_hints": ["Hint 1", "Hint 2", "Hint 3"],
                "detected_entities": ["Entity 1", "Entity 2"],
                "meeting_context": "Sales discussion",
                "sentiment": "positive"
            }
        """
        hints = []
        entity_names = []
        
        # Generate hints from entities
        for entity in entities:
            entity_names.append(entity.text)
            
            if entity.label in self.HINT_TEMPLATES:
                templates = self.HINT_TEMPLATES[entity.label]
                hint = random.choice(templates).format(entity=entity.text)
                if hint not in hints:
                    hints.append(hint)
        
        # Add generic hints if we don't have enough
        while len(hints) < max_hints:
            generic = random.choice(self.GENERIC_HINTS)
            if generic not in hints:
                hints.append(generic)
        
        # Limit hints
        hints = hints[:max_hints]
        
        # Analyze sentiment
        sentiment_result = self.analyze_sentiment(transcript) if transcript else {"sentiment": "neutral"}
        
        # Determine meeting context from entities
        if any(e.label == "product" for e in entities):
            context = "Product discussion detected"
        elif any(e.label == "organization" for e in entities):
            context = "Company/vendor discussion"
        elif any(e.label == "person" for e in entities):
            context = "Stakeholder conversation"
        else:
            context = "Sales meeting in progress"
        
        return {
            "quick_hints": hints,
            "detected_entities": entity_names[:5],  # Limit to 5
            "meeting_context": context,
            "sentiment": sentiment_result["sentiment"]
        }
    
    def get_battlecard(self, competitor_name: str, context: str = "") -> Dict:
        """
        Generate competitive battlecard for detected competitor.
        
        Returns:
            {
                "competitor": "AWS",
                "counter_points": ["Point 1", "Point 2", "Point 3"],
                "quick_response": "One-liner response"
            }
        """
        key = competitor_name.lower().strip()
        
        # Check for exact or partial match
        for db_key, data in self.BATTLECARD_DB.items():
            if db_key in key or key in db_key:
                return {
                    "competitor": competitor_name,
                    "counter_points": data["counter_points"],
                    "quick_response": data["quick_response"]
                }
        
        # Generic battlecard for unknown competitors
        return {
            "competitor": competitor_name,
            "counter_points": [
                f"Research {competitor_name}'s weaknesses",
                f"Highlight our unique value vs {competitor_name}",
                f"Ask what they like/dislike about {competitor_name}"
            ],
            "quick_response": f"Let's discuss how we compare to {competitor_name} specifically for your needs."
        }
    
    def detect_competitors(self, entities: List[ExtractedEntity]) -> List[str]:
        """
        Detect known competitors from entity list.
        
        Returns list of competitor names found.
        """
        known_competitors = [
            "aws", "amazon", "salesforce", "datadog", "microsoft", 
            "hubspot", "slack", "google", "oracle", "sap", "zendesk",
            "freshworks", "zoho", "monday", "asana", "jira", "atlassian"
        ]
        
        detected = []
        for entity in entities:
            if entity.label in ["organization", "product", "service"]:
                name_lower = entity.text.lower()
                for comp in known_competitors:
                    if comp in name_lower or name_lower in comp:
                        detected.append(entity.text)
                        break
        
        return detected


if __name__ == "__main__":
    # Standalone Test
    print("Running standalone GLiNER test...")
    service = GLiNERService()
    
    # Test entity extraction
    text = "I met with John Doe from AWS yesterday. We discussed their Datadog setup and Salesforce integration."
    entities = service.extract(text)
    print("\n--- Entities ---")
    for r in entities:
        print(f"  {r.label} -> {r.text} ({r.score:.2f})")
    
    # Test hint generation
    print("\n--- Hints ---")
    hints = service.generate_hints(entities, text)
    for h in hints["quick_hints"]:
        print(f"  • {h}")
    print(f"  Context: {hints['meeting_context']}")
    print(f"  Sentiment: {hints['sentiment']}")
    
    # Test competitor detection
    print("\n--- Competitors ---")
    competitors = service.detect_competitors(entities)
    for c in competitors:
        print(f"  ⚔️ {c}")
        bc = service.get_battlecard(c)
        print(f"     Response: {bc['quick_response']}")
