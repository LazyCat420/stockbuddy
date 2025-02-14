from langchain_community.utilities import SearxSearchWrapper
from typing import List, Dict
from config import SEARXNG_URL
from web_scraper import WebScraper
import pprint
import time
from ai_analysis import AIAnalyzer

class NewsSearcher:
    def __init__(self):
        self.searx = SearxSearchWrapper(
            searx_host=SEARXNG_URL,
            k=3  # Default number of results
        )
        # Initialize web scraper
        self.web_scraper = WebScraper()
        self.ai_analyzer = AIAnalyzer()
       
    
    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Core search function using SearxNG via LangChain"""
        try:
            print("\n=== Search Process Start ===")
            print(f"🔍 Query: {query}")
            print(f"📊 Max results requested: {max_results}")
            
            # Get results using LangChain's SearxNG wrapper
            results = self.searx.results(
                query,
                num_results=max_results,
                categories="news, finance"
            )
            
            print(f"\n📊 Found {len(results)} raw results")
            
            # Debug first raw result
            if results:
                print("\n🔍 First Raw Result:")
                print(f"Link: {results[0].get('link', 'No link')}")
                print(f"Title: {results[0].get('title', 'No title')}")
            
            # Process and format results with debugging
            processed_results = []
            for i, result in enumerate(results, 1):
                url = result.get('link', '')  # SearxNG uses 'link' for URL
                print(f"\n🔄 Processing result {i}/{len(results)}")
                print(f"URL found: {url}")
                
                processed_result = {
                    "title": result.get("title", ""),
                    "content": result.get("snippet", ""),
                    "url": url,  # Store the URL from 'link'
                    "source": result.get("engines", ["unknown"])[0],
                    "category": result.get("category", "news")
                }
                processed_results.append(processed_result)
                print(f"✅ Result {i} processed - URL stored: {processed_result['url']}")
            
            print(f"\n=== Search Process Complete ===")
            print(f"📝 Processed {len(processed_results)} results")
            return processed_results
            
        except Exception as e:
            print("\n❌ Error in search process:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print("\nTraceback:")
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
    
    def search_and_analyze(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for news and analyze the content of each article sequentially"""
        print("\n=== Starting News Search and Analysis ===")
        print(f"🔍 Query: {query}")
        print(f"📊 Max results: {max_results}")
        
        # Get initial search results
        results = self.search(query, max_results)
        print(f"\n📊 Found {len(results)} results to analyze")
        
        # Debug URLs before analysis
        print("\n🔍 URLs found for analysis:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.get('url', 'No URL')}")
        
        # Analyze each article one at a time
        analyzed_results = []
        
        for index, result in enumerate(results, 1):
            url = result.get("url")
            if not url:
                print(f"\n⚠️ Skipping result {index} - No URL found")
                continue
            
            print(f"\n=== Processing Article {index}/{len(results)} ===")
            print(f"📰 Title: {result.get('title', 'No title')}")
            print(f"🔗 URL being sent to web scraper: {url}")
            
            # Add delay between scraping attempts
            if index > 1:
                print("⏳ Waiting before next scrape...")
                time.sleep(5)
            
            # Scrape and analyze with debug log
            print(f"\n🔍 Sending URL to web scraper: {url}")
            scraped_data = self.web_scraper.scrape_and_analyze(url)
            
            if scraped_data["success"]:
                analysis = self.ai_analyzer.analyze_content(scraped_data)
                if analysis["success"]:
                    result.update({
                        "analysis": analysis["summary"],
                        "sentiment": analysis["sentiment"],
                        "key_points": analysis["key_points"]
                    })
                    analyzed_results.append(result)
                else:
                    print(f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}")
            else:
                print(f"❌ Scraping failed: {scraped_data.get('error', 'Unknown error')}")
        
        print(f"\n=== Analysis Complete ===")
        print(f"Successfully analyzed {len(analyzed_results)}/{len(results)} articles")
        return analyzed_results 