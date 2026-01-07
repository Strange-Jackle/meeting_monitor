from typing import List
from gliner import GLiNER
from app.modules.core.domain import EntityExtractor, ExtractedEntity
from app.core.config import settings

class GLiNERService(EntityExtractor):
    def __init__(self):
        print(f"Loading GLiNER model: {settings.GLINER_MODEL_NAME}...")
        self.model = GLiNER.from_pretrained(settings.GLINER_MODEL_NAME)
        self.labels = ["person", "email", "phone number", "organization", "location", "date", "product", "service"]
        print("GLiNER model loaded.")

    def extract(self, text: str) -> List[ExtractedEntity]:
        entities = self.model.predict_entities(text, self.labels)
        
        extracted = []
        for e in entities:
             extracted.append(ExtractedEntity(
                 text=e["text"],
                 label=e["label"],
                 score=e["score"]
             ))
        return extracted

if __name__ == "__main__":
    # Standalone Test
    print("Running standalone GLiNER test...")
    service = GLiNERService()
    text = "I met with John Doe from Acme Corp yesterday. His email is john.doe@example.com."
    results = service.extract(text)
    for r in results:
        print(f"Found: {r.label} -> {r.text} ({r.score:.2f})")
