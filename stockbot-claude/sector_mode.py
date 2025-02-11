from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
import json

class SectorMode:
    def __init__(self):
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
    
    def run(self, sector: str) -> Dict:
        """Run sector mode trading analysis"""
        try:
            print(f"\n=== Starting {sector.upper()} Sector Analysis ===")
            
            # Step 1: Get sector specific news
            print("\n1. Fetching sector news...")
            sector_news = self.news_searcher.search_sector_news(sector)
            print(f"Raw sector news data:")
            for i, news in enumerate(sector_news[:3], 1):
                print(f"\nArticle {i}:")
                print(f"  Title: {news.get('title', 'No title')}")
                print(f"  Source: {news.get('source', 'Unknown')}")
                print(f"  Content: {news.get('content', 'No content')[:200]}...")
            self._save_news(sector_news, sector)
            
            # Step 2: Analyze sector news
            print("\n2. Analyzing sector news...")
            sector_analysis = self.ai_analyzer.analyze_news(sector_news)
            print("\nSector Analysis Results:")
            print(f"  Sentiment: {sector_analysis.get('sentiment', 'unknown')}")
            print(f"  Confidence: {sector_analysis.get('confidence', 0)}%")
            print("  Key Points:")
            for point in sector_analysis.get('key_points', []):
                print(f"    - {point}")
            
            # Step 3: Get stocks in sector
            print("\n3. Getting stocks in sector...")
            sector_stocks = self.stock_data.get_sector_stocks(sector)
            print(f"Found {len(sector_stocks)} stocks in {sector} sector: {', '.join(sector_stocks)}")
            
            if not sector_stocks:
                print(f"WARNING: No stocks found for sector: {sector}")
                print("Checking sector mapping in stock_data.py...")
                # Print available sectors from stock_data.py
                available_sectors = self.stock_data.get_available_sectors()
                print(f"Available sectors: {', '.join(available_sectors)}")
            
            self.db.update_watchlist(sector_stocks, sector)
            
            # Step 4: Analyze each stock in sector
            print("\n4. Analyzing individual stocks...")
            trading_decisions = []
            for ticker in sector_stocks:
                print(f"\nAnalyzing {ticker}...")
                decision = self._analyze_stock(ticker, sector_analysis)
                if decision:
                    print(f"  Decision for {ticker}:")
                    print(f"    Action: {decision['decision']['action']}")
                    print(f"    Confidence: {decision['decision']['confidence']}%")
                    print(f"    Personality: {decision['personality']}")
                    trading_decisions.append(decision)
                else:
                    print(f"  Failed to analyze {ticker}")
            
            # Step 5: Generate summary
            print("\n5. Generating sector summary...")
            summary = self._generate_summary(trading_decisions, sector_analysis, sector)
            print("\nSector Summary:")
            print(json.dumps(summary, indent=2))
            self.db.save_summary("sector", trading_decisions, summary)
            
            return {
                "success": True,
                "sector": sector,
                "stocks_analyzed": sector_stocks,
                "decisions": trading_decisions,
                "summary": summary
            }
            
        except Exception as e:
            print(f"\nError in sector mode: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news: List[Dict], sector: str) -> None:
        """Save sector news to database"""
        print(f"Saving {len(news)} news articles for {sector} sector to database...")
        for article in news:
            self.db.save_news(sector.upper(), article, article.get("source", "unknown"))
    
    def _analyze_stock(self, ticker: str, sector_analysis: Dict) -> Dict:
        """Analyze individual stock in sector context"""
        try:
            # Get stock specific news
            print(f"Getting news for {ticker}...")
            stock_news = self.news_searcher.search_stock_news(ticker)
            print(f"Found {len(stock_news)} news articles for {ticker}")
            if stock_news:
                print("Latest headlines:")
                for news in stock_news[:2]:
                    print(f"  - {news.get('title', 'No title')}")
            self._save_news(stock_news, f"STOCK_{ticker}")
            
            # Get stock data
            print(f"Getting stock data for {ticker}...")
            stock_data = self.stock_data.get_stock_data(ticker)
            if not stock_data["success"]:
                print(f"Failed to get stock data: {stock_data.get('error', 'Unknown error')}")
                return None
            
            print("Stock data retrieved successfully:")
            print(f"  Current Price: ${stock_data.get('current_price', 0):.2f}")
            print(f"  Daily Change: {stock_data.get('daily_change', 0):.2f}%")
            
            # Combine sector and stock news for analysis
            print("Combining sector and stock analysis...")
            combined_news = stock_news + [{
                "title": "Sector Analysis",
                "content": sector_analysis.get("market_impact", ""),
                "source": "sector_analysis"
            }]
            
            # Analyze combined news
            news_analysis = self.ai_analyzer.analyze_news(combined_news)
            print(f"Combined analysis sentiment: {news_analysis.get('sentiment', 'unknown')}")
            
            # Select trading personality
            print("Selecting trading personality...")
            personality = self.ai_analyzer.select_trading_personality()
            print(f"Selected personality: {personality}")
            
            # Generate trading decision
            print("Generating trading decision...")
            decision = self.ai_analyzer.generate_trading_decision(
                ticker=ticker,
                news_analysis=news_analysis,
                stock_data=stock_data,
                personality=personality
            )
            
            # Save trade if action is buy or sell
            if decision["action"] in ["buy", "sell"]:
                print(f"Saving {decision['action']} trade for {ticker}...")
                self.db.save_trade(
                    ticker=ticker,
                    action=decision["action"],
                    price=decision["entry_price"],
                    quantity=decision["quantity"],
                    personality=personality,
                    confidence=decision["confidence"],
                    stop_loss=decision["stop_loss"],
                    take_profit=decision["take_profit"]
                )
            
            return {
                "ticker": ticker,
                "decision": decision,
                "personality": personality
            }
            
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