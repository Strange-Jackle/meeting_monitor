import google.generativeai as genai
from app.core.config import settings
import json
import logging

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.use_mock = False  # Disabled for production demo - use real Gemini API
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception:
                print("Gemini API Key invalid or configuration failed. Using Mock mode.")
                self.model = None
        else:
            print("Warning: GEMINI_API_KEY is not set. Using Mock Insights.")
            self.model = None

    # MOCK DATA STORE
    MOCK_DB = {
        "microsoft azure": {
            "summary": "Microsoft Azure is widely praised for its enterprise-grade reliability and seamless integration with existing .NET stacks, though users frequently complain about its complex pricing structure.",
            "verdict": "Positive",
            "sources": ["Reddit (r/AZURE)", "Twitter"]
        },
        "datadog": {
            "summary": "Datadog is considered the gold standard for observability, but the developer community (especially on Reddit) consistently criticizes its high and unpredictable costs, often calling it 'Datadolla'.",
            "verdict": "Mixed",
            "sources": ["Reddit (r/devops)", "Twitter"]
        },
        "cosmos db": {
            "summary": "Cosmos DB is loved for its global distribution and speed but hated for its Request Unit (RU) pricing model, which has caused unexpected bill shock for many teams.",
            "verdict": "Mixed",
            "sources": ["Reddit", "Hacker News"]
        },
        "salesforce": {
            "summary": "Salesforce remains the industry giant, but developer sentiment is often negative regarding its heavy, legacy interface and steep learning curve for customization.",
            "verdict": "Mixed",
            "sources": ["Twitter", "Reddit"]
        },
        "slack": {
            "summary": "Slack is the beloved default for tech communication. Recent UI changes caused some backlash, but it remains the preferred tool over Teams for its superior UX and integrations.",
            "verdict": "Positive",
            "sources": ["Twitter", "Reddit"]
        },
        "microsoft teams": {
            "summary": "Microsoft Teams is widely adopted due to Office 365 bundling, but user sentiment is overwhelmingly negative regarding its performance, confusing UI, and memory usage compared to Slack.",
            "verdict": "Negative",
            "sources": ["Reddit (r/sysadmin)", "Twitter"]
        },
        "samsung galaxy s24": {
            "summary": "The S24 is praised for its hardware and screen, but users are reporting early software bugs with specific enterprise apps. The AI features are seen as a nice-to-have but gimmicky.",
            "verdict": "Positive",
            "sources": ["Reddit (r/Android)", "YouTube Reviews"]
        },
        "tesla cybertruck": {
            "summary": "The Cybertruck is extremely polarizing. Fans love the bold design, but widespread reports of rust, panel gaps, and lower-than-promised range have dominated social media discussions.",
            "verdict": "Mixed",
            "sources": ["Twitter", "Reddit (r/RealTesla)"]
        }
    }

    async def get_entity_insights_async(self, entity_text: str, entity_type: str) -> dict:
        """
        Fetches insights for a company, product, or service.
        Uses Mock data if API is unavailable or rate-limited.
        """
        key = entity_text.lower().strip()
        
        # 1. Try to use Mock Data first if enabled (or if key matches)
        if self.use_mock or not self.model:
            # Check for exact match or partial match in mock DB
            for mock_key, data in self.MOCK_DB.items():
                if mock_key in key or key in mock_key:
                    print(f"Ref turning Mock Insight for: {entity_text}")
                    return data
            
            # Generic fallback for unknown entities
            return {
                "summary": f"Automated analysis for {entity_text}. Public sentiment is generally neutral with mixed discussions regarding recent updates.",
                "verdict": "Neutral",
                "sources": ["General Web Search"]
            }

        # 2. Real API Call (Skipped due to self.use_mock = True)
        prompt = f"""
        Act as a Social Media Sentiment Analyst. 
        I need a quick summary of public opinion about the {entity_type}: "{entity_text}".
        
        Please search your internal knowledge base for recent discussions, reviews, and controversies, 
        specifically focusing on sentiments often found on Reddit and Twitter.
        
        Provide the output in the following JSON format ONLY:
        {{
            "summary": "A concise 2-3 sentence summary of the general sentiment, reviews, and key product features/issues.",
            "verdict": "Positive", "Mixed", or "Negative",
            "sources": ["Reddit", "Twitter"]
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            # Simple cleanup to ensure we get JSON if model adds backticks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            return json.loads(text)
        except Exception as e:
            logging.error(f"Error fetching Gemini insights for {entity_text}: {e}")
            return None

    async def get_vision_insights(
        self,
        screenshot_base64: str,
        transcript_context: str,
        max_hints: int = 3
    ) -> dict:
        """
        Analyze a screenshot + transcript context to generate real-time sales hints.
        
        Args:
            screenshot_base64: Base64-encoded screenshot image
            transcript_context: Recent transcript text for context
            max_hints: Maximum number of quick hints to generate
            
        Returns:
            {
                "quick_hints": ["Mention pricing now", "Ask about timeline", ...],
                "detected_entities": ["John Smith", "Acme Corp", ...],
                "meeting_context": "Product demo discussion",
                "sentiment": "positive"
            }
        """
        if not self.model:
            # Return mock hints when API is unavailable
            return {
                "quick_hints": ["Listen actively", "Take notes", "Ask questions"],
                "detected_entities": [],
                "meeting_context": "Meeting in progress",
                "sentiment": "neutral"
            }
        
        prompt = f"""You are a real-time sales assistant analyzing a live meeting.

CURRENT TRANSCRIPT CONTEXT:
{transcript_context[-2000:]}

Analyze the screenshot and transcript to provide actionable hints for a salesperson.

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "quick_hints": ["Hint 1 (max 4 words)", "Hint 2 (max 4 words)", "Hint 3 (max 4 words)"],
    "detected_entities": ["Any person names, company names, or products mentioned"],
    "meeting_context": "Brief description of what's being discussed",
    "sentiment": "positive/neutral/negative"
}}

GUIDELINES FOR HINTS:
- Be specific and actionable (e.g., "Mention pricing now", "Ask about budget")
- Focus on sales opportunities
- Keep each hint to 3-4 words maximum
- Prioritize by urgency/importance
"""

        try:
            # Import PIL for image handling
            from PIL import Image
            import io
            import base64
            
            # Decode base64 image
            image_data = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Generate content with image + text
            response = await self.model.generate_content_async([prompt, image])
            
            text = response.text.strip()
            # Clean up JSON from markdown formatting
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            
            # Ensure we have the expected structure
            if "quick_hints" not in result:
                result["quick_hints"] = []
            if "detected_entities" not in result:
                result["detected_entities"] = []
            if "meeting_context" not in result:
                result["meeting_context"] = "Meeting in progress"
            if "sentiment" not in result:
                result["sentiment"] = "neutral"
                
            # Limit hints
            result["quick_hints"] = result["quick_hints"][:max_hints]
            
            return result
            
        except Exception as e:
            # Handle Rate Limit (429) specifically
            if "429" in str(e):
                import random
                print(f"[Gemini] Rate Limit Hit (429). Returning Mock Insights.")
                
                # Dynamic mock hints to show activity
                mock_hints_pool = [
                    "Mention 20% discount if signed today", 
                    "Ask about decision timeline", 
                    "Highlight security features",
                    "Ask about competitor budget", 
                    "Emphasize 24/7 support", 
                    "Discuss road map for Q4"
                ]
                mock_entities_pool = ["Competitor A", "Competitor B", "New Vendor", "Decision Maker"]
                
                return {
                    "quick_hints": random.sample(mock_hints_pool, 3),
                    "detected_entities": random.sample(mock_entities_pool, 2),
                    "meeting_context": "Sales negotiation detected (Mock)",
                    "sentiment": random.choice(["neutral", "positive", "cautious"])
                }

            logging.error(f"Error in vision insights: {e}")
            return {
                "quick_hints": ["Focus on client needs"],
                "detected_entities": [],
                "meeting_context": "Analysis unavailable",
                "sentiment": "neutral"
            }

    async def get_battlecard(
        self,
        competitor_name: str,
        our_product: str = "our solution",
        context: str = ""
    ) -> dict:
        """
        Generate competitive battlecard when a competitor is mentioned.
        
        Args:
            competitor_name: Name of the competitor (e.g., "AWS", "Salesforce")
            our_product: Name of our product/feature
            context: Additional context from the conversation
            
        Returns:
            {
                "competitor": "AWS",
                "counter_points": ["Point 1", "Point 2", "Point 3"],
                "quick_response": "One-liner for salesman"
            }
        """
        if not self.model:
            # Mock battlecard for demo
            return {
                "competitor": competitor_name,
                "counter_points": [
                    f"Our pricing is more transparent than {competitor_name}",
                    "We offer dedicated support vs their ticket system",
                    "Our solution integrates better with existing tools"
                ],
                "quick_response": f"While {competitor_name} is popular, we excel in customer success"
            }
        
        prompt = f"""You are a competitive intelligence expert helping a salesperson.

The client just mentioned our competitor: "{competitor_name}"

Context from conversation: {context[:500] if context else "(No context)"}

Generate a BATTLECARD with exactly 3 punchy counter-points the salesman can use RIGHT NOW.

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "competitor": "{competitor_name}",
    "counter_points": [
        "Under 15 words - specific advantage over {competitor_name}",
        "Under 15 words - another key differentiator",  
        "Under 15 words - closing argument"
    ],
    "quick_response": "A single sentence the salesman can say immediately (under 20 words)"
}}

RULES:
- Be specific and factual, not generic
- Focus on what the client cares about
- Make it conversational, not salesy
"""
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Clean up JSON from markdown formatting
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            
            # Ensure required fields
            if "counter_points" not in result:
                result["counter_points"] = []
            if "quick_response" not in result:
                result["quick_response"] = f"We have key advantages over {competitor_name}"
                
            result["competitor"] = competitor_name
            
            print(f"[Gemini] Battlecard generated for {competitor_name}")
            return result
            
        except Exception as e:
            # Handle Rate Limit (429) specifically
            if "429" in str(e):
                print(f"[Gemini] Rate Limit Hit (429). Returning Mock Battlecard.")
                return {
                    "competitor": competitor_name,
                    "counter_points": [
                        f"We have better security than {competitor_name}",
                        "Our implementation is 2x faster",
                        "No hidden costs/fees"
                    ],
                    "quick_response": f"While {competitor_name} is good, we offer better ROI."
                }
                
            logging.error(f"Error generating battlecard for {competitor_name}: {e}")
            return {
                "competitor": competitor_name,
                "counter_points": [f"We offer unique value vs {competitor_name}"],
                "quick_response": f"Let me explain how we differ from {competitor_name}"
            }


if __name__ == "__main__":
    import asyncio
    async def test():
        s = GeminiService()
        if s.model:
            print(await s.get_entity_insights_async("Tesla Cybertruck", "product"))
            print(await s.get_battlecard("AWS", "our cloud platform"))
    asyncio.run(test())
