from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
import json

class GeneralMode:
    def __init__(self):
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
    
    def run(self) -> Dict:
        """Run general mode trading analysis"""
        try:
            print("\n=== Starting General Market Analysis ===")
            
            # Step 1: Get general market news
            print("\n1. Fetching general market news...")
            market_news = self.news_searcher.search_market_news()
            print(f"Found {len(market_news)} news articles")
            if market_news:
                print("Sample news headlines:")
                for i, news in enumerate(market_news[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')} - {news.get('source', 'Unknown source')}")
            self._save_news(market_news)
            
            # Step 2: Analyze news and identify potential tickers
            print("\n2. Analyzing market news...")
            news_analysis = self.ai_analyzer.analyze_news(market_news)
            print("News Analysis Results:")
            print(f"  Sentiment: {news_analysis.get('sentiment', 'unknown')}")
            print(f"  Confidence: {news_analysis.get('confidence', 0)}%")
            print("  Key Points:")
            for point in news_analysis.get('key_points', []):
                print(f"    - {point}")
            
            # Step 3: Generate watchlist from news analysis
            print("\n3. Generating watchlist from news analysis...")
            watchlist = self._generate_watchlist(news_analysis)
            print(f"Generated watchlist with {len(watchlist)} tickers: {', '.join(watchlist)}")
            self.db.update_watchlist(watchlist)
            
            # Step 4: Analyze each stock in watchlist
            print("\n4. Analyzing individual stocks...")
            trading_decisions = []
            for ticker in watchlist:
                print(f"\nAnalyzing {ticker}...")
                decision = self._analyze_stock(ticker)
                if decision:
                    print(f"  Decision for {ticker}:")
                    print(f"    Action: {decision['decision']['action']}")
                    print(f"    Confidence: {decision['decision']['confidence']}%")
                    print(f"    Personality: {decision['personality']}")
                    trading_decisions.append(decision)
                else:
                    print(f"  Failed to analyze {ticker}")
            
            # Step 5: Generate summary
            print("\n5. Generating trading summary...")
            summary = self._generate_summary(trading_decisions, news_analysis)
            print("Summary:")
            print(json.dumps(summary, indent=2))
            self.db.save_summary("general", trading_decisions, summary)
            
            return {
                "success": True,
                "watchlist": watchlist,
                "decisions": trading_decisions,
                "summary": summary
            }
            
        except Exception as e:
            print(f"\nError in general mode: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news: List[Dict]) -> None:
        """Save news to database"""
        print(f"Saving {len(news)} news articles to database...")
        for article in news:
            self.db.save_news("MARKET", article, article.get("source", "unknown"))
    
    def _generate_watchlist(self, news_analysis: Dict) -> List[str]:
        """Generate watchlist from news analysis"""
        print("Extracting potential tickers from news analysis...")
        # Extract potential tickers from news analysis key points
        tickers = set()
        for point in news_analysis.get("key_points", []):
            # This is a simplified version. In production, you'd want more sophisticated ticker extraction
            words = point.split()
            for word in words:
                if word.isupper() and len(word) >= 2 and len(word) <= 5:
                    print(f"Found potential ticker: {word}")
                    tickers.add(word)
        
        print(f"\nValidating {len(tickers)} potential tickers...")
        # Validate tickers using yfinance
        valid_tickers = []
        for ticker in tickers:
            print(f"Validating {ticker}...")
            data = self.stock_data.get_stock_data(ticker, period="1d")
            if data["success"]:
                print(f"✓ {ticker} is valid")
                valid_tickers.append(ticker)
            else:
                print(f"✗ {ticker} is invalid: {data.get('error', 'Unknown error')}")
        
        return valid_tickers[:10]  # Limit to top 10 tickers
    
    def _analyze_stock(self, ticker: str) -> Dict:
        """Analyze individual stock and generate trading decision"""
        try:
            # Get stock specific news
            print(f"Getting news for {ticker}...")
            stock_news = self.news_searcher.search_stock_news(ticker)
            print(f"Found {len(stock_news)} news articles for {ticker}")
            self._save_news(stock_news)
            
            # Get stock data
            print(f"Getting stock data for {ticker}...")
            stock_data = self.stock_data.get_stock_data(ticker)
            if not stock_data["success"]:
                print(f"Failed to get stock data: {stock_data.get('error', 'Unknown error')}")
                return None
            
            # Analyze news
            print(f"Analyzing news for {ticker}...")
            news_analysis = self.ai_analyzer.analyze_news(stock_news)
            
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
    
    def _generate_summary(self, decisions: List[Dict], market_analysis: Dict) -> Dict:
        """Generate trading session summary"""
        buy_decisions = [d for d in decisions if d["decision"]["action"] == "buy"]
        sell_decisions = [d for d in decisions if d["decision"]["action"] == "sell"]
        hold_decisions = [d for d in decisions if d["decision"]["action"] == "hold"]
        
        return {
            "market_sentiment": market_analysis.get("sentiment", "neutral"),
            "market_confidence": market_analysis.get("confidence", 0),
            "total_decisions": len(decisions),
            "buy_decisions": len(buy_decisions),
            "sell_decisions": len(sell_decisions),
            "hold_decisions": len(hold_decisions),
            "average_confidence": sum(d["decision"]["confidence"] for d in decisions) / len(decisions) if decisions else 0,
            "timestamp": str(datetime.now())
        } 