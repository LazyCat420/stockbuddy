from langchain_community.utilities import SearxSearchWrapper
from typing import List, Dict
from config import SEARXNG_URL
import pprint

class NewsSearcher:
    def __init__(self):
        self.searx = SearxSearchWrapper(
            searx_host=SEARXNG_URL,
            k=10  # Default number of results
        )
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Core search function using SearxNG via LangChain
        Returns results with snippet, title, link, engines, and category
        """
        try:
            print(f"\nSearching for: {query}")
            # Get results using LangChain's SearxNG wrapper
            results = self.searx.results(
                query,
                num_results=max_results,
                categories="news, finance"  # Focus on news category
            )
            
            print(f"Found {len(results)} results")
            # Debug first result
            if results:
                print("Sample result:")
                pprint.pprint(results[0])
            
            # Process and format results
            processed_results = []
            for result in results:
                processed_results.append({
                    "title": result.get("title", ""),
                    "content": result.get("snippet", ""),  # SearxNG uses 'snippet' for content
                    "url": result.get("link", ""),  # SearxNG uses 'link' for URL
                    "source": result.get("engines", ["unknown"])[0],  # First engine is usually the source
                    "category": result.get("category", "news")
                })
            
            return processed_results
            
        except Exception as e:
            print(f"Error searching news: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return []
    
    def search_stock_news(self, ticker: str, query: str = "") -> List[Dict]:
        """Search for stock-specific news"""
        search_query = f"{ticker} stock market news {query}".strip()
        results = self.search(search_query)
        print(f"Found {len(results)} news articles for {ticker}")
        return self.remove_duplicates(results)
    
    def search_sector_news(self, sector: str, query: str = "") -> List[Dict]:
        """Search for sector-specific news"""
        search_query = f"{sector} sector stock market {query}".strip()
        results = self.search(search_query)
        print(f"Found {len(results)} news articles for {sector} sector")
        return self.remove_duplicates(results)
    
    def search_market_news(self, query: str = "") -> List[Dict]:
        """Search for general market news"""
        # Use multiple queries to get diverse results
        queries = [
            "stock market analysis latest news",
            "financial market trends today",
            "stock market movement analysis",
            "market sentiment indicators"
        ]
        
        all_results = []
        for q in queries:
            search_query = f"{q} {query}".strip()
            results = self.search(search_query, max_results=5)
            all_results.extend(results)
            print(f"Found {len(results)} results for query: {search_query}")
        
        # Remove duplicates and return top results
        unique_results = self.remove_duplicates(all_results, limit=15)
        print(f"Total unique market news articles: {len(unique_results)}")
        return unique_results
    
    def remove_duplicates(self, results: List[Dict], limit: int = 10) -> List[Dict]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break
        
        return unique_results 