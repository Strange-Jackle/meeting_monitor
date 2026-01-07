import asyncio
from duckduckgo_search import DDGS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging
import random

class WebInsightService:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        # DDGS instance moved to local scope in _search_ddg to avoid threading issues

    async def get_entity_insights_async(self, entity_text: str, entity_type: str) -> dict:
        """
        Fetches insights by searching DuckDuckGo for recent Reddit/Twitter discussions
        and analyzing sentiment locally with VADER.
        """
        print(f"Searching web for: {entity_text}...")
        
        # 1. Construct Search Query (Simplified for better hits)
        # Complex OR queries can fail in DDG API wrappers sometimes
        query = f'{entity_text} review sentiment reddit twitter'
        
        results = []
        try:
            # Run blocking DDG search in a separate thread
            # max_results=5 is enough to get a pulse
            results = await asyncio.to_thread(self._search_ddg, query)
        except Exception as e:
            logging.error(f"DDG Search failed for {entity_text}: {e}")
            return None

        if not results:
            print(f"No web results found for {entity_text}")
            return None

        # 2. Analyze Sentiment Locally (VADER)
        # Aggregate text from titles and snippets
        full_text = " ".join([f"{r.get('title','')} {r.get('body','')}" for r in results])
        scores = self.analyzer.polarity_scores(full_text)
        compound_score = scores['compound']
        
        # Determine Verdict
        verdict = "Mixed"
        if compound_score > 0.05:
            verdict = "Positive"
        elif compound_score < -0.05:
            verdict = "Negative"

        # 3. Generate Summary from Snippets
        # Take the most relevant snippet or just the top one
        top_snippet = results[0].get('body', results[0].get('title', ''))
        if len(top_snippet) > 150:
            top_snippet = top_snippet[:150] + "..."
            
        summary = f"Recent discussions trend {verdict.lower()}. Top comment: \"{top_snippet}\""

        # 4. Extract Sources (Domains)
        sources = set()
        for r in results:
            link = r.get('href', '')
            if "reddit.com" in link:
                sources.add("Reddit")
            elif "twitter.com" in link or "x.com" in link:
                sources.add("Twitter")
        
        if not sources:
            sources.add("Web")

        return {
            "summary": summary,
            "verdict": verdict,
            "sources": list(sources)
        }

    def _search_ddg(self, query):
        """Helper to run the synchronous DDG generator"""
        # Instantiate DDGS here for thread safety
        with DDGS() as ddgs:
            # ddgs.text() returns a generator, consume it to get a list
            return list(ddgs.text(query, max_results=5))

    async def get_detailed_insights_async(self, entity_text: str) -> dict:
        """
        Fetches deeper insights:
        1. Recent News Headlines
        2. Pros/Cons snapshot
        """
        print(f"Deep diving into: {entity_text}...")
        
        try:
            results = await asyncio.to_thread(self._search_details_ddg, entity_text)
            return results
        except Exception as e:
            logging.error(f"Detailed search failed: {e}")
            return {"error": str(e)}

    def _search_details_ddg(self, entity):
        """Helper for granular searches"""
        news_items = []
        pros_cons = []
        
        with DDGS() as ddgs:
            # 1. News Search
            # ddgs.news returns a generator
            news_gen = ddgs.news(keywords=entity, max_results=3)
            for r in news_gen:
                news_items.append({
                    "title": r.get('title'),
                    "url": r.get('url'),
                    "date": r.get('date'),
                    "source": r.get('source')
                })
            
            # 2. Pros/Cons Text Search
            # We look for "reviews" or "pros cons" specifically
            query = f"{entity} pros cons review summary"
            text_gen = ddgs.text(query, max_results=3)
            for r in text_gen:
                # Simple extraction of body text
                body = r.get('body', '')
                if body:
                    pros_cons.append(body)

        return {
            "news": news_items,
            "analysis": pros_cons
        }

if __name__ == "__main__":
    async def test():
        s = WebInsightService()
        print(await s.get_entity_insights_async("Cosmos DB", "service"))
    asyncio.run(test())
