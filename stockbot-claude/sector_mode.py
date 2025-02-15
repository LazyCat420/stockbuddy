from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
from utils.console_colors import console
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
            print(f"\n{console.title(f'=== Starting {sector.upper()} Sector Analysis ===')}")
            
            # Step 1: Get sector specific news
            print(f"\n{console.title('1. Fetching sector news...')}")
            sector_news = self.news_searcher.search_sector_news(sector)
            print(f"{console.info(f'Found {len(sector_news)} news articles for {sector} sector')}")
            self._save_news(sector_news, sector)
            
            # Step 2: Analyze sector news
            print(f"\n{console.title('2. Analyzing sector news...')}")
            sector_analysis = self.ai_analyzer.analyze_news(sector_news)
            
            # Step 3: Extract tickers from news and get additional sector stocks
            print(f"\n{console.title('3. Identifying relevant stocks...')}")
            news_tickers = self._extract_tickers_from_news(sector_news)
            sector_stocks = self.stock_data.get_sector_stocks(sector)
            
            # Combine and deduplicate tickers
            all_tickers = list(set(news_tickers + sector_stocks))
            print(f"{console.info(f'Total unique stocks to analyze: {len(all_tickers)}')}")
            
            # Update watchlist in database
            self.db.update_watchlist(all_tickers, sector)
            print(f"{console.success(f'Watchlist updated for {sector}: {all_tickers}')}")
            
            # Step 4: Analyze each stock with deep analysis
            print(f"\n{console.title('4. Performing deep analysis on each stock...')}")
            trading_decisions = []
            for ticker in all_tickers:
                print(f"\n{console.info(f'Analyzing {console.ticker(ticker)}...')}")
                decision = self._analyze_stock(ticker, sector_analysis)
                if decision:
                    trading_decisions.append(decision)
            
            # Step 5: Generate summary
            print(f"\n{console.title('5. Generating sector summary...')}")
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

            # Get AI response
            response = self.ai_analyzer._generate_response(prompt)
            
            try:
                # Clean up response to ensure it's valid JSON
                response = response.strip()
                if not response.startswith("{"):
                    start_idx = response.find("{")
                    if start_idx != -1:
                        response = response[start_idx:]
                    else:
                        print(f"{console.warning('No valid JSON found in response')}")
                        return []
                
                # Parse JSON
                analysis = json.loads(response)
                
                # Extract and validate tickers with yfinance
                valid_tickers = []
                for ticker_info in analysis.get("identified_tickers", []):
                    ticker = ticker_info.get("ticker")
                    confidence = ticker_info.get("confidence", 0)
                    
                    if ticker and confidence >= 80:  # Only include high confidence tickers
                        print(f"\n{console.info(f'Validating {console.ticker(ticker)}...')}")
                        try:
                            # Use yfinance to validate ticker
                            data = self.stock_data.get_stock_data(ticker, period="1d")
                            if data["success"] and data.get("data") is not None:
                                print(f"{console.success(f'✓ {ticker} is valid ({confidence}% confidence)')}")
                                valid_tickers.append(ticker)
                            else:
                                print(f"{console.error(f'✗ {ticker} is invalid - no data found')}")
                        except Exception as e:
                            print(f"{console.error(f'✗ Error validating {ticker}: {str(e)}')}")
                            continue
                
                if not valid_tickers:
                    print(f"{console.warning('No valid tickers found in news articles')}")
                else:
                    print(f"{console.success(f'Found {len(valid_tickers)} valid tickers')}")
                
                return valid_tickers
                
            except json.JSONDecodeError as e:
                print(f"{console.error(f'Error parsing JSON response: {str(e)}')}")
                print(f"{console.warning('Raw response:')}")
                print(response)
                return []
                
        except Exception as e:
            print(f"{console.error(f'Error extracting tickers: {str(e)}')}")
            import traceback
            print(f"{console.error('Traceback:')}")
            print(f"{console.error(traceback.format_exc())}")
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
        initial_stock_analysis = self.ai_analyzer.analyze_news(initial_news)
        
        # Create initial summary as formatted string
        current_summary = f"""
        Sector Context:
        - Market Impact: {sector_analysis.get('market_impact', '')}
        - Sentiment: {sector_analysis.get('sentiment', 'neutral')}
        - Key Points: {', '.join(sector_analysis.get('key_points', []))}
        
        Initial Stock Analysis:
        - Market Impact: {initial_stock_analysis.get('market_impact', '')}
        - Sentiment: {initial_stock_analysis.get('sentiment', 'neutral')}
        - Key Points: {', '.join(initial_stock_analysis.get('key_points', []))}
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
                print(f"\nQuestion {i}: {question.get('text', '')}")
                
                # Search news with the specific question
                question_news = self.news_searcher.search_stock_news(ticker, question.get('text', ''))
                self._save_news(question_news, f"{ticker}_R{round_num + 1}")
                
                # Analyze the news to answer the question
                answer_analysis = self.ai_analyzer.analyze_news(question_news)
                print(f"Answer sentiment: {answer_analysis.get('sentiment', 'unknown')}")
                
                round_findings["questions"].append(question)
                round_findings["answers"].append(answer_analysis)
                
                # Update current summary with new insights - ensure we're adding strings
                if answer_analysis and isinstance(answer_analysis, dict):
                    new_context = f"""
                    New Analysis:
                    - Market Impact: {answer_analysis.get('market_impact', '')}
                    - Sentiment: {answer_analysis.get('sentiment', 'neutral')}
                    - Key Points: {', '.join(answer_analysis.get('key_points', []))}
                    """
                    current_summary += "\n" + new_context
            
            all_findings["rounds"].append(round_findings)
            
            # Extract key insights from this round
            for answer in round_findings["answers"]:
                if isinstance(answer, dict) and "key_points" in answer:
                    all_findings["key_insights"].extend(answer["key_points"])
        
        return all_findings
    
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