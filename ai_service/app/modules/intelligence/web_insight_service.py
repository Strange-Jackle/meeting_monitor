import asyncio
import warnings
import os

# Suppress DDG rename warning BEFORE import (at module level)
os.environ['PYTHONWARNINGS'] = 'ignore::RuntimeWarning'
warnings.filterwarnings("ignore", message=".*has been renamed.*", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*duckduckgo.*", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from duckduckgo_search import DDGS

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging
import random
try:
    import trafilatura
except ImportError:
    trafilatura = None
    print("[Web] Note: trafilatura not installed. Run: pip install trafilatura")

class WebInsightService:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

    async def get_negative_insights_stream(self, entity_text: str):
        """
        Generator that streams insights:
        1. Yields FAST snippets (T+1s)
        2. Yields DEEP crawl data (T+2s+)
        """
        print(f"[Web] Starting Negative Deep Dive for: {entity_text}")
        
        # T+0: Fire 3 Parallel Negative Queries (Optimized for English)
        queries = [
            f'"{entity_text}" problems complaints issues english',
            f'"{entity_text}" cons downsides limitations english',
            f'"{entity_text}" worst features reddit' 
        ]
        
        # Run searches in parallel
        tasks = [asyncio.to_thread(self._search_ddg, q) for q in queries]
        results_lists = await asyncio.gather(*tasks)
        
        # Flatten results
        all_results = []
        for r_list in results_lists:
            all_results.extend(r_list)
            
        if not all_results:
            print(f"[Web] No results found for {entity_text}")
            yield {"type": "fast", "data": None}
            return

        # T+1: FAST Analysis (VADER on snippets)
        # ------------------------------------------------
        # Filter for English-looking content (Latin Character Ratio)
        def is_mostly_english(item):
            text = (item.get('title', '') + " " + item.get('body', '')).strip()
            if not text: return False
            try:
                # Count latin letters [a-zA-Z]
                latin_count = sum(1 for c in text if 'a' <= c.lower() <= 'z')
                ratio = latin_count / len(text)
                return ratio >= 0.5
            except:
                return True

        # Blacklist unhelpful/non-English domains
        BLACKLIST_DOMAINS = [
            "wikipedia.org", "login.", "signin.", "signup.", 
            "facebook.com", "instagram.com",
            # Chinese sites
            "zhidao.baidu.com", "baidu.com", "zhihu.com", 
            "weibo.com", "tieba.baidu.com", "sogou.com", "163.com",
            # Other non-English
            "yandex.", ".ru/", ".cn/", ".jp/"
        ]
        
        # Priority domains (sorted first)
        PRIORITY_DOMAINS = ["reddit.com", "x.com", "twitter.com", "news.ycombinator.com", "medium.com"]
        
        def is_useful_source(url):
            return not any(b in url.lower() for b in BLACKLIST_DOMAINS)
        
        def get_priority(url):
            """Lower number = higher priority"""
            url_lower = url.lower()
            for i, domain in enumerate(PRIORITY_DOMAINS):
                if domain in url_lower:
                    return i
            return 100  # Default low priority

        # Filter and deduplicate
        unique_results = {r['href']: r for r in all_results 
            if is_mostly_english(r) and is_useful_source(r['href'])
        }.values()
        
        # Sort by priority (Reddit/X first)
        sorted_results = sorted(unique_results, key=lambda r: get_priority(r['href']))
        top_results = sorted_results[:5]
        
        if not top_results:
             print("[Web] No English results found after filter.")
             yield {"type": "fast", "data": None}
             return

        snippet_text = " ".join([f"{r.get('title','')} {r.get('body','')}" for r in top_results])
        scores = self.analyzer.polarity_scores(snippet_text)
        
        fast_insight = {
            "summary": f"Initial scan of {len(all_results)} sources shows potential issues. Top Top complaint: '{top_results[0].get('body','')[:100]}...'",
            "verdict": "Negative" if scores['compound'] < -0.05 else "Mixed",
            "negative_score": round(scores['neg'] * 10, 1),
            "sources": [r.get('href') for r in top_results[:3]]
        }
        
        yield {"type": "fast", "data": fast_insight}
        
        # T+2: DEEP Crawl (Trafilatura)
        # ------------------------------------------------
        if not trafilatura:
            print("[Web] Trafilatura not installed, skipping deep crawl.")
            return

        print(f"[Web] Deep Crawling top {len(top_results[:2])} URLs...")
        
        crawl_tasks = [asyncio.to_thread(self._crawl_url, r['href']) for r in top_results[:2]]
        crawled_texts = await asyncio.gather(*crawl_tasks)
        
        # Filter for purely negative content / facts
        combined_text = "\n\n".join([t for t in crawled_texts if t]) # trafilatura already filtered by lang='en'
        
        # Simple extraction of "bad" keywords lines
        negative_keywords = [
            "slow", "expensive", "crash", "bug", "support", "fail", "hard", 
            "complex", "limit", "hidden", "money", "cost", "price", "down", 
            "error", "bad", "fix", "issue", "problem", "suck", "terrible"
        ]
        critical_points = []
        
        for line in combined_text.split('\n'):
            if len(line) > 30 and any(k in line.lower() for k in negative_keywords):
                critical_points.append(line.strip())
        
        # Select unique top 3 points
        critical_points = list(set(critical_points))[:3]
        
        if critical_points:
            deep_insight = {
                "summary": "Deep analysis found specific complaints:\n• " + "\n• ".join(critical_points),
                "verdict": "Confirmed Negative",
                "evidence": critical_points,
                "sources": [r.get('href') for r in top_results[:2]]
            }
            yield {"type": "deep", "data": deep_insight}
        else:
            print("[Web] Crawl yielded no specific negative points.")

    def _search_ddg(self, query):
        """Run DDG search safely (English only, US region)"""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with DDGS() as ddgs:
                    # Force English results with region parameter
                    return list(ddgs.text(
                        query, 
                        region='us-en',  # US English results only
                        max_results=15   # Get more to allow filtering
                    ))
        except Exception as e:
            logging.error(f"DDG error for '{query}': {e}")
            return []

    def _crawl_url(self, url):
        """Download and extract text from URL"""
        try:
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                # Keep target_language='en' as it happens after fetch
                return trafilatura.extract(downloaded, include_comments=False, favor_precision=True, target_language='en')
        except Exception as e:
            logging.error(f"Crawl error {url}: {e}")
        return ""

if __name__ == "__main__":
    async def test():
        s = WebInsightService()
        async for update in s.get_negative_insights_stream("Datadog"):
            print(f"\n--- {update['type'].upper()} UPDATE ---")
            print(update['data'])
    asyncio.run(test())
