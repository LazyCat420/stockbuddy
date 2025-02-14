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
        """Run sector mode trading analysis with enhanced stock analysis"""
        try:
            print(f"\n=== Starting {sector.upper()} Sector Analysis ===")
            
            # Step 1: Get sector specific news
            print("\n1. Fetching sector news...")
            sector_news = self.news_searcher.search_sector_news(sector)
            print(f"Found {len(sector_news)} news articles for {sector} sector")
            self._save_news(sector_news, sector)
            
            # Step 2: Analyze sector news
            print("\n2. Analyzing sector news...")
            sector_analysis = self.ai_analyzer.analyze_news(sector_news)
            
            # Step 3: Extract tickers from news and get additional sector stocks
            print("\n3. Identifying relevant stocks...")
            news_tickers = self._extract_tickers_from_news(sector_news)
            sector_stocks = self.stock_data.get_sector_stocks(sector)
            
            # Combine and deduplicate tickers
            all_tickers = list(set(news_tickers + sector_stocks))
            print(f"Total unique stocks to analyze: {len(all_tickers)}")
            
            # Update watchlist in database
            self.db.update_watchlist(all_tickers, sector)
            
            # Step 4: Analyze each stock with deep analysis
            print("\n4. Performing deep analysis on each stock...")
            trading_decisions = []
            for ticker in all_tickers:
                decision = self._analyze_stock(ticker, sector_analysis)
                if decision:
                    trading_decisions.append(decision)
            
            # Step 5: Generate summary
            print("\n5. Generating sector summary...")
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
    
    def _extract_tickers_from_news(self, news_articles: List[Dict]) -> List[str]:
        """Extract ticker symbols from news articles using AI analysis"""
        print("\nExtracting tickers from news articles...")
        try:
            # Create a prompt for ticker extraction
            prompt = f"""Analyze these news articles and identify stock ticker symbols mentioned:

News articles:
{json.dumps(news_articles, indent=2)}

Follow these steps:
1. Identify any company names and their stock tickers
2. Verify that each ticker is a valid stock symbol (2-5 capital letters)
3. Rank tickers by relevance and mention frequency
4. Return only the most relevant tickers

Provide your analysis in JSON format:
{{
    "identified_tickers": ["TICKER1", "TICKER2", ...],
    "company_mentions": [
        {{"company": "Company Name", "ticker": "TICK", "relevance": "high/medium/low"}}
    ]
}}

Think through each step carefully and explain your reasoning."""

            # Get AI response
            response = self.ai_analyzer._generate_response(prompt)
            analysis = json.loads(response)
            
            # Extract tickers
            tickers = analysis.get("identified_tickers", [])
            print(f"\nFound {len(tickers)} potential tickers:")
            for company in analysis.get("company_mentions", []):
                print(f"- {company['ticker']} ({company['company']}, Relevance: {company['relevance']})")
            
            # Validate tickers using yfinance
            valid_tickers = []
            for ticker in tickers:
                print(f"\nValidating {ticker}...")
                data = self.stock_data.get_stock_data(ticker, period="1d")
                if data["success"]:
                    print(f"✓ {ticker} is valid")
                    # Do deep analysis on validated ticker
                    detailed_analysis = self._deep_stock_analysis(ticker, {})
                    if detailed_analysis:
                        valid_tickers.append(ticker)
                else:
                    print(f"✗ {ticker} is invalid: {data.get('error', 'Unknown error')}")
            
            return valid_tickers

        except Exception as e:
            print(f"Error extracting tickers: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return []
    
    def _deep_stock_analysis(self, ticker: str, sector_analysis: Dict) -> Dict:
        """Perform deep analysis through multiple rounds of questioning"""
        print(f"\nStarting deep analysis for {ticker}...")
        
        all_findings = {
            "rounds": [],
            "key_insights": []
        }
        
        # Start with initial stock news and sector context
        initial_news = self.news_searcher.search_stock_news(ticker)
        self._save_news(initial_news, f"STOCK_{ticker}")
        
        # Get stock data
        stock_data = self.stock_data.get_stock_data(ticker)
        if not stock_data.get("success", False):
            print(f"Failed to get stock data for {ticker}")
            return None
        
        # Initial analysis combining stock and sector insights
        current_summary = f"""
        Sector Context: {sector_analysis.get('market_impact', '')}
        Initial Stock Analysis: {self.ai_analyzer.analyze_news(initial_news).get('market_impact', '')}
        """
        
        print("\nStarting multi-round analysis...")
        # Perform 2 rounds of follow-up questions
        for round_num in range(2):
            print(f"\nRound {round_num + 1}:")
            round_findings = {
                "questions": [],
                "answers": []
            }
            
            # Generate follow-up questions based on current context
            questions = self.ai_analyzer.generate_follow_up_questions(ticker, current_summary)
            print(f"Generated {len(questions)} follow-up questions")
            
            # Search for answers to each question
            for i, question in enumerate(questions, 1):
                print(f"\nQuestion {i}: {question}")
                
                # Search news with the specific question
                question_news = self.news_searcher.search_stock_news(ticker, question)
                self._save_news(question_news, f"{ticker}_R{round_num + 1}")
                
                # Analyze the news to answer the question
                answer_analysis = self.ai_analyzer.analyze_news(question_news)
                print(f"Answer sentiment: {answer_analysis.get('sentiment', 'unknown')}")
                
                round_findings["questions"].append(question)
                round_findings["answers"].append(answer_analysis)
                
                # Update current summary with new insights
                current_summary += f"\n{answer_analysis.get('market_impact', '')}"
            
            all_findings["rounds"].append(round_findings)
            
            # Extract key insights from this round
            for answer in round_findings["answers"]:
                if isinstance(answer, dict) and "key_points" in answer:
                    all_findings["key_insights"].extend(answer["key_points"])
        
        # Make final trading decision
        print("\nGenerating final trading decision...")
        
        # Combine all insights
        all_insights = []
        for round_data in all_findings["rounds"]:
            for answer in round_data["answers"]:
                if isinstance(answer, dict):
                    all_insights.append({
                        "sentiment": answer.get("sentiment", "neutral"),
                        "market_impact": answer.get("market_impact", ""),
                        "confidence": answer.get("confidence", 0)
                    })
        
        # Calculate average sentiment and confidence
        sentiments = [i["sentiment"] for i in all_insights]
        confidences = [i["confidence"] for i in all_insights]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Select trading personality
        personality = self.ai_analyzer.select_trading_personality()
        print(f"Selected personality: {personality}")
        
        # Generate final trading decision
        decision = self.ai_analyzer.generate_trading_decision(
            ticker=ticker,
            news_analysis={
                "sentiment": max(set(sentiments), key=sentiments.count),
                "confidence": avg_confidence,
                "key_points": all_findings["key_insights"],
                "market_impact": "\n".join(i["market_impact"] for i in all_insights)
            },
            stock_data=stock_data,
            personality=personality
        )
        
        # Save trade if action is buy
        if decision.get("action") == "buy":
            print(f"\nSaving buy decision for {ticker}...")
            self.db.save_trade(
                ticker=ticker,
                action="buy",
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
            "personality": personality,
            "analysis": all_findings
        }
    
    def _analyze_stock(self, ticker: str, sector_analysis: Dict) -> Dict:
        """Enhanced stock analysis with deep questioning"""
        try:
            print(f"\nAnalyzing {ticker}...")
            
            # Get initial stock news and data
            print(f"Getting initial news for {ticker}...")
            stock_news = self.news_searcher.search_stock_news(ticker)
            print(f"Found {len(stock_news)} news articles")
            self._save_news(stock_news, f"STOCK_{ticker}")
            
            # Get stock data
            print(f"Getting stock data for {ticker}...")
            stock_data = self.stock_data.get_stock_data(ticker)
            if not stock_data.get("success", False):
                print(f"Failed to get stock data: {stock_data.get('error', 'Unknown error')}")
                return None
            
            # Perform deep analysis
            detailed_analysis = self._deep_stock_analysis(ticker, sector_analysis)
            print(f"Completed deep analysis with {len(detailed_analysis['rounds'])} rounds")
            
            # Select trading personality based on the analysis
            print("Selecting trading personality...")
            personality = self.ai_analyzer.select_trading_personality()
            print(f"Selected personality: {personality}")
            
            # Combine all insights for final decision
            all_insights = []
            for round_data in detailed_analysis["rounds"]:
                for answer in round_data["answers"]:
                    if isinstance(answer, dict):
                        all_insights.append({
                            "sentiment": answer.get("sentiment", "neutral"),
                            "market_impact": answer.get("market_impact", ""),
                            "confidence": answer.get("confidence", 0)
                        })
            
            # Generate final trading decision
            print("Generating trading decision...")
            decision = self.ai_analyzer.generate_trading_decision(
                ticker=ticker,
                news_analysis={
                    "sentiment": sector_analysis.get("sentiment", "neutral"),
                    "confidence": sector_analysis.get("confidence", 0),
                    "key_points": detailed_analysis["key_insights"],
                    "market_impact": "\n".join(i["market_impact"] for i in all_insights)
                },
                stock_data=stock_data,
                personality=personality
            )
            
            # Save trade if action is buy or sell
            if decision.get("action") in ["buy", "sell"]:
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
                "personality": personality,
                "detailed_analysis": detailed_analysis
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