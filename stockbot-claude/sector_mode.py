from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
from utils.console_colors import console
import json
import time
from single_stock_mode import SingleStockMode

class SectorMode:
    def __init__(self):
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
    
    def run(self, sector: str) -> Dict:
        """Run sector mode trading analysis with enhanced stock analysis"""
        try:
            print(f"\n{console.title(f'=== Starting {sector.upper()} Sector Analysis ===')}")
            
            # Step 1: Get sector specific news
            print(f"\n{console.title('1. Fetching sector news...')}")
            sector_news = self.news_searcher.search_sector_news(sector)
            print(f"{console.info(f'Found {len(sector_news)} news articles for {sector} sector')}")
            self._save_news(sector_news, sector)
            
            # Step 2: Process each article with LLM summarization
            print(f"\n{console.title('2. Summarizing news articles...')}")
            summarized_articles = []
            for i, article in enumerate(sector_news, 1):
                print(f"\nProcessing article {i}/{len(sector_news)}...")
                if article.get("content"):
                    analysis = self.ai_analyzer.analyze_content({
                        "success": True,
                        "content": article["content"],
                        "metadata": {"source": article.get("source", "unknown")}
                    })
                    if analysis["success"]:
                        summarized_articles.append({
                            "summary": analysis["summary"],
                            "sentiment": analysis["sentiment"],
                            "key_points": analysis["key_points"],
                            "market_impact": analysis.get("market_impact", "")
                        })
                        print(f"✅ Article {i} summarized")
                        print(f"Sentiment: {analysis['sentiment']}")
                        print(f"Key points: {len(analysis['key_points'])}")
                    else:
                        print(f"⚠️ Failed to analyze article {i}: {analysis.get('error', 'Unknown error')}")
                else:
                    print(f"⚠️ Article {i} has no content")
            
            # Step 3: Run chain-of-thought analysis on summaries
            print(f"\n{console.title('3. Running chain-of-thought analysis...')}")
            sector_analysis = self.ai_analyzer.analyze_news(summarized_articles)
            
            # Step 4: Extract tickers from news and get additional sector stocks
            print(f"\n{console.title('4. Identifying relevant stocks...')}")
            news_tickers = self._extract_tickers_from_news(sector_news)
            sector_stocks = self.stock_data.get_sector_stocks(sector)
            
            # Combine and deduplicate tickers
            all_tickers = list(set(news_tickers + sector_stocks))
            print(f"{console.info(f'Total unique stocks to analyze: {len(all_tickers)}')}")
            
            # Update watchlist in database
            self.db.update_watchlist(all_tickers, sector)
            print(f"{console.success(f'Watchlist updated for {sector}: {all_tickers}')}")
            
            # Step 5: Analyze each stock with deep analysis
            print(f"\n{console.title('5. Performing deep analysis on each stock...')}")
            trading_decisions = []
            for ticker in all_tickers:
                print(f"\n{console.info(f'Analyzing {console.ticker(ticker)}...')}")
                decision = self._analyze_stock(ticker, sector_analysis)
                if decision:
                    trading_decisions.append(decision)
            
            # Step 6: Generate summary
            print(f"\n{console.title('6. Generating sector summary...')}")
            summary = self._generate_summary(trading_decisions, sector_analysis, sector)
            self.db.save_summary("sector", trading_decisions, summary)
            
            return {
                "success": True,
                "sector": sector,
                "stocks_analyzed": all_tickers,
                "decisions": trading_decisions,
                "summary": summary
            }
            
        except Exception as e:
            print(f"\n{console.error(f'Error in sector mode: {str(e)}')}")
            import traceback
            print(f"{console.error('Traceback:')}")
            print(f"{console.error(traceback.format_exc())}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news: List[Dict], sector: str) -> None:
        """Save sector news to database"""
        print(f"Saving {len(news)} news articles for {sector} sector to database...")
        for article in news:
            self.db.save_news(sector.upper(), article, article.get("source", "unknown"))
    
    def _extract_tickers_from_news(self, news_articles: List[Dict]) -> List[str]:
        """Extract and validate ticker symbols from news articles using AI analysis and yfinance"""
        print(f"\n{console.title('Extracting tickers from news articles...')}")
        try:
            # Create a prompt for ticker extraction
            prompt = f"""Analyze these news articles and identify stock ticker symbols mentioned.
Only include valid stock tickers (1-5 capital letters) that you are highly confident about.
Format your response as a valid JSON object with this exact structure:

{{
    "identified_tickers": [
        {{
            "ticker": "AAPL",
            "company": "Apple Inc",
            "sector": "TECHNOLOGY",
            "confidence": 95
        }}
    ]
}}

Only include tickers you are very confident about. If no valid tickers are found, return an empty array.
Do not include any explanatory text outside the JSON structure.

News articles to analyze:
{json.dumps([{
    "title": article.get("title", ""),
    "content": article.get("content", ""),
    "source": article.get("source", "unknown")
} for article in news_articles], indent=2)}"""

            # Get AI response with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.ai_analyzer._generate_response(prompt)
                    response = response.strip()
                    
                    # Clean up response to ensure it's valid JSON
                    if not response.startswith("{"):
                        start_idx = response.find("{")
                        if start_idx != -1:
                            response = response[start_idx:]
                        else:
                            print(f"{console.warning('No valid JSON found in response')}")
                            if attempt < max_retries - 1:
                                print(f"Retrying... (Attempt {attempt + 2}/{max_retries})")
                                time.sleep(1)  # Add delay between retries
                                continue
                            return []
                    
                    # Parse JSON
                    analysis = json.loads(response)
                    
                    # Extract tickers and get their data (but don't validate)
                    valid_tickers = []
                    for ticker_info in analysis.get("identified_tickers", []):
                        ticker = ticker_info.get("ticker", "").strip().upper()
                        confidence = ticker_info.get("confidence", 0)
                        
                        if ticker and confidence >= 80:  # Only include high confidence tickers
                            print(f"\n{console.info(f'Getting data for {console.ticker(ticker)}...')}")
                            try:
                                # Get stock data for later analysis
                                time.sleep(0.5)  # Add delay between API calls
                                data = self.stock_data.get_stock_data(ticker, period="1d")
                                valid_tickers.append(ticker)
                                print(f"{console.success(f'✓ Added {ticker} ({confidence}% confidence)')}")
                            except Exception as e:
                                print(f"{console.warning(f'⚠️ Could not get data for {ticker}, but including it anyway')}")
                                valid_tickers.append(ticker)
                    
                    if not valid_tickers:
                        print(f"{console.warning('No valid tickers found in news articles')}")
                    else:
                        tickers_str = ", ".join(valid_tickers)
                        print(f"{console.success(f'Found {len(valid_tickers)} valid tickers: {tickers_str}')}")
                    
                    return valid_tickers
                    
                except json.JSONDecodeError as e:
                    print(f"{console.error(f'Error parsing JSON response: {str(e)}')}")
                    print(f"{console.warning('Raw response:')}")
                    print(response)
                    if attempt < max_retries - 1:
                        print(f"Retrying... (Attempt {attempt + 2}/{max_retries})")
                        time.sleep(1)
                        continue
                    return []
                
        except Exception as e:
            print(f"{console.error(f'Error extracting tickers: {str(e)}')}")
            import traceback
            print(f"{console.error('Traceback:')}")
            print(f"{console.error(traceback.format_exc())}")
            return []
    
    def _analyze_stock(self, ticker: str, sector_analysis: Dict) -> Dict:
        """Enhanced stock analysis with deep questioning"""
        try:
            print(f"\nAnalyzing {ticker}...")
            
            # Initialize and use SingleStockMode for detailed analysis
            single_stock = SingleStockMode()
            result = single_stock.run(ticker)
            
            if not result["success"]:
                print(f"Failed to analyze {ticker}: {result.get('error', 'Unknown error')}")
                return None
            
            # Add sector context to the analysis
            result["sector_context"] = {
                "sector": sector_analysis.get("sector", "unknown"),
                "sector_sentiment": sector_analysis.get("sentiment", "neutral"),
                "sector_confidence": sector_analysis.get("confidence", 0),
                "sector_key_points": sector_analysis.get("key_points", [])
            }
            
            # Log analysis status
            if result.get("has_market_data", False):
                print(f"✅ Completed analysis for {ticker} with market data")
            else:
                print(f"✅ Completed analysis for {ticker} with news only")
            
            return result
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return None
    
    def _generate_summary(self, decisions: List[Dict], sector_analysis: Dict, sector: str) -> Dict:
        """Generate sector trading session summary"""
        buy_decisions = [d for d in decisions if d["decision"]["action"] == "buy"]
        sell_decisions = [d for d in decisions if d["decision"]["action"] == "sell"]
        hold_decisions = [d for d in decisions if d["decision"]["action"] == "hold"]
        
        return {
            "sector": sector,
            "sector_sentiment": sector_analysis.get("sentiment", "neutral"),
            "sector_confidence": sector_analysis.get("confidence", 0),
            "total_stocks": len(decisions),
            "buy_decisions": len(buy_decisions),
            "sell_decisions": len(sell_decisions),
            "hold_decisions": len(hold_decisions),
            "average_confidence": sum(d["decision"]["confidence"] for d in decisions) / len(decisions) if decisions else 0,
            "key_points": sector_analysis.get("key_points", []),
            "timestamp": str(datetime.now())
        } 