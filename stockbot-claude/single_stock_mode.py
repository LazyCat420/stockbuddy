from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
import json

class SingleStockMode:
    def __init__(self):
        print("\n=== Initializing Single Stock Mode ===")
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
        print("✅ Single Stock Mode initialized")
    
    def run(self, ticker: str) -> Dict:
        """Run single stock trading analysis"""
        try:
            print(f"\n🔍 Starting analysis for {ticker}...")
            
            # Step 1: Get initial stock news and data
            print(f"\n📰 Searching news for {ticker}...")
            stock_news = self.news_searcher.search_and_analyze(f"{ticker} stock market news")
            print(f"Found {len(stock_news)} news articles")
            
            print(f"\n📊 Fetching stock data for {ticker}...")
            stock_data = self.stock_data.get_stock_data(ticker)
            has_stock_data = stock_data.get("success", False)
            
            if not has_stock_data:
                print(f"⚠️ Could not fetch market data for {ticker}, continuing with news analysis only")
                stock_data = {
                    "success": True,
                    "ticker": ticker,
                    "current_price": 0,
                    "daily_change": 0,
                    "volume": 0,
                    "technical_indicators": {
                        "sma_20": 0,
                        "sma_50": 0,
                        "rsi": 0
                    }
                }
            
            # Step 2: Process analyzed news
            print("\n🔄 Processing news articles...")
            analyzed_articles = []
            for i, article in enumerate(stock_news):
                print(f"\nProcessing article {i+1}:")
                if article.get("analysis"):
                    print("✅ Article has analysis")
                    analyzed_articles.append({
                        "summary": article["analysis"],
                        "sentiment": article["sentiment"],
                        "key_points": article["key_points"]
                    })
                    print(f"Sentiment: {article['sentiment']}")
                    print(f"Key points: {len(article['key_points'])} points")
                else:
                    print("⚠️ Article missing analysis")
            
            print(f"\n📊 Analyzing {len(analyzed_articles)} processed articles...")
            initial_analysis = self.ai_analyzer.analyze_news(analyzed_articles)
            
            print("\n💾 Saving news to database...")
            self._save_news(stock_news, ticker)
            
            # Step 3: Generate and answer follow-up questions
            print("\n🔍 Starting deep analysis...")
            detailed_analysis = self._deep_analysis(ticker, initial_analysis)
            
            # Step 4: Make trading decision
            print("\n🎯 Generating trading decision...")
            trading_decision = self._make_trading_decision(
                ticker,
                stock_data,
                detailed_analysis
            )
            
            # Step 5: Generate summary
            print("\n📝 Generating final summary...")
            summary = self._generate_summary(ticker, trading_decision, detailed_analysis)
            
            print("\n💾 Saving summary to database...")
            self.db.save_summary("single_stock", [trading_decision], summary)
            
            print("\n✅ Analysis complete!")
            return {
                "success": True,
                "ticker": ticker,
                "has_market_data": has_stock_data,
                "decision": trading_decision,
                "analysis": detailed_analysis,
                "summary": summary
            }
            
        except Exception as e:
            print(f"\n❌ Error in single stock mode: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news: List[Dict], ticker: str) -> None:
        """Save stock news to database"""
        try:
            for article in news:
                self.db.save_news(f"STOCK_{ticker}", article, article.get("source", "unknown"))
            print(f"✅ Saved {len(news)} articles to database")
        except Exception as e:
            print(f"⚠️ Error saving news: {str(e)}")
    
    def _deep_analysis(self, ticker: str, initial_context: str) -> Dict:
        """Perform deep analysis through multiple rounds of questioning"""
        print("\n=== Starting Deep Analysis ===")
        all_findings = {
            "rounds": [],
            "key_insights": []
        }
        
        # Convert initial context to string if it's a dict
        if isinstance(initial_context, dict):
            current_summary = f"""
            Market Impact: {initial_context.get('market_impact', '')}
            Sentiment: {initial_context.get('sentiment', 'neutral')}
            Key Points: {', '.join(initial_context.get('key_points', []))}
            """
        else:
            current_summary = str(initial_context)
        
        # Perform multiple rounds of analysis
        for round_num in range(2):
            print(f"\n🔄 Analysis Round {round_num + 1}:")
            round_findings = {
                "questions": [],
                "answers": [],
                "tools_used": []
            }
            
            # Generate targeted questions
            print("\n❓ Generating targeted questions...")
            questions = self.ai_analyzer.generate_follow_up_questions(ticker, current_summary)
            print(f"Generated {len(questions)} questions")
            
            for i, q in enumerate(questions):
                print(f"\n📝 Question {i+1}: {q.get('text', '')}")
                print(f"🔧 Using research tool: {q.get('tool', 'unknown')}")
                
                # Use appropriate research tool
                try:
                    tool = q.get('tool', '').lower()
                    if 'news_search' in tool:
                        results = self.news_searcher.search_stock_news(ticker, q.get('text', ''))
                    elif 'financial_data' in tool:
                        results = self.stock_data.get_detailed_financials(ticker)
                    elif 'market_analysis' in tool:
                        results = self.stock_data.get_market_analysis(ticker)
                    else:
                        # Default to news search if tool is unknown
                        results = self.news_searcher.search_stock_news(ticker, q.get('text', ''))
                        tool = 'news_search'
                    
                    print("✅ Got research results")
                    
                    # Analyze results
                    print("🔄 Analyzing results...")
                    analysis = self.ai_analyzer.analyze_content({
                        "success": True,
                        "content": str(results),
                        "metadata": {"source": tool}
                    })
                    
                    round_findings["questions"].append(q)
                    round_findings["answers"].append(analysis)
                    round_findings["tools_used"].append(tool)
                    
                    # Update context for next questions - ensure we're adding strings
                    if analysis and isinstance(analysis, dict):
                        new_context = f"""
                        Market Impact: {analysis.get('market_impact', '')}
                        Sentiment: {analysis.get('sentiment', {}).get('direction', 'neutral')}
                        Key Points: {', '.join(analysis.get('key_points', []))}
                        """
                        current_summary += "\n" + new_context
                    
                except Exception as e:
                    print(f"⚠️ Error processing question: {str(e)}")
            
            all_findings["rounds"].append(round_findings)
            
            # Extract key insights
            print("\n🔑 Extracting key insights...")
            for answer in round_findings["answers"]:
                if answer.get("success"):
                    all_findings["key_insights"].extend(answer.get("key_points", []))
        
        print(f"\n✅ Deep analysis complete with {len(all_findings['key_insights'])} key insights")
        return all_findings
    
    def _make_trading_decision(self, ticker: str, stock_data: Dict, detailed_analysis: Dict) -> Dict:
        """Generate final trading decision based on deep analysis"""
        print("\n=== Generating Trading Decision ===")
        
        # Combine all insights for final analysis
        all_insights = []
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        total_confidence = 0
        confidence_count = 0
        
        # Process insights from each round
        for round_data in detailed_analysis.get("rounds", []):
            for answer in round_data.get("answers", []):
                if isinstance(answer, dict):
                    # Extract sentiment
                    if isinstance(answer.get("sentiment"), dict):
                        sentiment = answer["sentiment"].get("direction", "neutral")
                    else:
                        sentiment = answer.get("sentiment", "neutral")
                    sentiment_counts[sentiment.lower()] += 1
                    
                    # Extract confidence
                    if isinstance(answer.get("confidence"), (int, float)):
                        total_confidence += answer["confidence"]
                        confidence_count += 1
                    
                    # Add to insights
                    all_insights.append({
                        "sentiment": sentiment,
                        "market_impact": answer.get("market_impact", ""),
                        "key_points": answer.get("key_points", [])
                    })
        
        print(f"\n📊 Analyzing {len(all_insights)} insights")
        
        # Calculate dominant sentiment and average confidence
        dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 50
        
        print(f"Dominant sentiment: {dominant_sentiment}")
        print(f"Average confidence: {avg_confidence:.2f}%")
        
        # Select trading personality
        print("\n👤 Selecting trading personality...")
        personality = self.ai_analyzer.select_trading_personality()
        print(f"Selected personality: {personality}")
        
        # Generate final trading decision with enforced JSON structure
        print("\n🎯 Generating final decision...")
        decision_prompt = f"""As a {personality} trader, analyze this data and make a trading decision:

Ticker: {ticker}
Sentiment: {dominant_sentiment}
Confidence: {avg_confidence}%
Key Insights: {json.dumps(detailed_analysis.get("key_insights", []))}
Market Impact: {json.dumps([i.get("market_impact", "") for i in all_insights if i.get("market_impact")])}
Stock Data: {json.dumps(stock_data)}

Format your decision as JSON:
{{
    "action": "buy/sell/hold",
    "confidence": 0-100,
    "quantity": "number of shares",
    "entry_price": "suggested entry price",
    "stop_loss": "suggested stop loss price",
    "take_profit": "suggested take profit price",
    "reasoning": {{
        "technical_factors": ["factor1", "factor2"],
        "fundamental_factors": ["factor1", "factor2"],
        "risk_factors": ["factor1", "factor2"],
        "decision_process": "detailed explanation"
    }},
    "scenarios": {{
        "best_case": "description",
        "worst_case": "description",
        "most_likely": "description"
    }},
    "risk_assessment": {{
        "risk_level": "low/medium/high",
        "key_risks": ["risk1", "risk2"],
        "mitigation_strategies": ["strategy1", "strategy2"]
    }}
}}"""
        
        try:
            decision = json.loads(self.ai_analyzer._generate_response(decision_prompt))
        except json.JSONDecodeError:
            print("⚠️ Error parsing decision JSON, using default hold decision")
            decision = {
                "action": "hold",
                "confidence": 0,
                "quantity": 0,
                "entry_price": 0,
                "stop_loss": 0,
                "take_profit": 0,
                "reasoning": {
                    "technical_factors": [],
                    "fundamental_factors": [],
                    "risk_factors": [],
                    "decision_process": "Error generating decision"
                },
                "scenarios": {
                    "best_case": "Unknown",
                    "worst_case": "Unknown",
                    "most_likely": "Unknown"
                },
                "risk_assessment": {
                    "risk_level": "high",
                    "key_risks": ["Decision generation failed"],
                    "mitigation_strategies": ["Manual review required"]
                }
            }
        
        # Save trade if action is buy or sell
        if decision.get("action") in ["buy", "sell"]:
            print("\n💾 Saving trade to database...")
            
            # Prepare trade data with analysis
            analysis_data = {
                "sentiment": dominant_sentiment,
                "avg_confidence": avg_confidence,
                "key_insights": detailed_analysis.get("key_insights", []),
                "market_impact": decision.get("market_impact", ""),
                "technical_factors": decision.get("reasoning", {}).get("technical_factors", []),
                "fundamental_factors": decision.get("reasoning", {}).get("fundamental_factors", []),
                "risk_factors": decision.get("reasoning", {}).get("risk_factors", []),
                "decision_process": decision.get("reasoning", {}).get("decision_process", ""),
                "scenarios": decision.get("scenarios", {}),
                "risk_assessment": decision.get("risk_assessment", {})
            }
            
            # Save to MongoDB
            try:
                self.db.save_trade(
                    ticker=ticker,
                    action=decision["action"],
                    price=decision.get("entry_price", 0),
                    quantity=decision.get("quantity", 0),
                    personality=personality,
                    confidence=decision.get("confidence", 0),
                    stop_loss=decision.get("stop_loss", 0),
                    take_profit=decision.get("take_profit", 0),
                    analysis=analysis_data
                )
                print("✅ Trade saved to MongoDB")
            except Exception as e:
                print(f"⚠️ Failed to save trade to MongoDB: {str(e)}")
            
            # Save to ChromaDB with proper datetime handling
            try:
                if hasattr(self.ai_analyzer, 'chroma_handler') and self.ai_analyzer.chroma_handler:
                    # Convert datetime to string in trade data
                    chroma_trade_data = {
                        "ticker": ticker,
                        "action": decision["action"],
                        "price": decision.get("entry_price", 0),
                        "quantity": decision.get("quantity", 0),
                        "personality": personality,
                        "confidence": decision.get("confidence", 0),
                        "stop_loss": decision.get("stop_loss", 0),
                        "take_profit": decision.get("take_profit", 0),
                        "timestamp": str(datetime.now()),
                        "status": "open",
                        "analysis": analysis_data
                    }
                    
                    self.ai_analyzer.chroma_handler.save_document(
                        collection_name="trades",  # Changed from trading_decisions to trades
                        document=json.dumps(chroma_trade_data, indent=4),
                        metadata={
                            "ticker": ticker,
                            "action": decision["action"],
                            "timestamp": str(datetime.now()),
                            "personality": personality,
                            "status": "open"
                        }
                    )
                    print("✅ Trade saved to ChromaDB")
            except Exception as e:
                print(f"⚠️ Failed to save trade to ChromaDB: {str(e)}")
        
        print("\n✅ Trading decision complete")
        return {
            "ticker": ticker,
            "decision": decision,
            "personality": personality,
            "analysis_summary": {
                "sentiment": dominant_sentiment,
                "confidence": avg_confidence,
                "insights_analyzed": len(all_insights)
            }
        }
    
    def _generate_summary(self, ticker: str, trading_decision: Dict, detailed_analysis: Dict) -> Dict:
        """Generate single stock analysis summary"""
        print("\n=== Generating Final Summary ===")
        summary = {
            "ticker": ticker,
            "action": trading_decision["decision"]["action"],
            "confidence": trading_decision["decision"]["confidence"],
            "personality": trading_decision["personality"],
            "analysis_rounds": len(detailed_analysis["rounds"]),
            "total_questions_analyzed": sum(len(r["questions"]) for r in detailed_analysis["rounds"]),
            "key_insights": detailed_analysis["key_insights"],
            "risk_assessment": trading_decision["decision"]["risk_assessment"],
            "timestamp": str(datetime.now())
        }
        
        print(f"\n📊 Summary Stats:")
        print(f"Action: {summary['action'].upper()}")
        print(f"Confidence: {summary['confidence']}%")
        print(f"Analysis rounds: {summary['analysis_rounds']}")
        print(f"Questions analyzed: {summary['total_questions_analyzed']}")
        print(f"Key insights: {len(summary['key_insights'])}")
        
        return summary 