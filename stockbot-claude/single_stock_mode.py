from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler

class SingleStockMode:
    def __init__(self):
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
    
    def run(self, ticker: str) -> Dict:
        """Run single stock trading analysis"""
        try:
            # Step 1: Get initial stock news and data
            stock_news = self.news_searcher.search_stock_news(ticker)
            stock_data = self.stock_data.get_stock_data(ticker)
            
            if not stock_data["success"]:
                return {
                    "success": False,
                    "error": f"Could not fetch data for {ticker}"
                }
            
            # Step 2: Initial news analysis
            initial_analysis = self.ai_analyzer.analyze_news(stock_news)
            self._save_news(stock_news, ticker)
            
            # Step 3: Generate and answer follow-up questions (2 rounds)
            detailed_analysis = self._deep_analysis(ticker, initial_analysis)
            
            # Step 4: Make trading decision
            trading_decision = self._make_trading_decision(
                ticker,
                stock_data,
                detailed_analysis
            )
            
            # Step 5: Generate summary
            summary = self._generate_summary(ticker, trading_decision, detailed_analysis)
            self.db.save_summary("single_stock", [trading_decision], summary)
            
            return {
                "success": True,
                "ticker": ticker,
                "decision": trading_decision,
                "analysis": detailed_analysis,
                "summary": summary
            }
            
        except Exception as e:
            print(f"Error in single stock mode: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news: List[Dict], ticker: str) -> None:
        """Save stock news to database"""
        for article in news:
            self.db.save_news(f"STOCK_{ticker}", article, article.get("source", "unknown"))
    
    def _deep_analysis(self, ticker: str, initial_analysis: Dict) -> Dict:
        """Perform deep analysis through multiple rounds of questioning"""
        all_findings = {
            "rounds": [],
            "key_insights": []
        }
        
        current_summary = initial_analysis.get("market_impact", "")
        
        # Perform 2 rounds of follow-up questions
        for round_num in range(2):
            round_findings = {
                "questions": [],
                "answers": []
            }
            
            # Generate follow-up questions
            questions = self.ai_analyzer.generate_follow_up_questions(ticker, current_summary)
            
            # Search for answers to each question
            for question in questions:
                # Search news with the question
                question_news = self.news_searcher.search_stock_news(ticker, question)
                self._save_news(question_news, f"{ticker}_R{round_num + 1}")
                
                # Analyze the news to answer the question
                answer_analysis = self.ai_analyzer.analyze_news(question_news)
                
                round_findings["questions"].append(question)
                round_findings["answers"].append(answer_analysis)
                
                # Update current summary with new insights
                current_summary += f"\n{answer_analysis.get('market_impact', '')}"
            
            all_findings["rounds"].append(round_findings)
            
            # Extract key insights from this round
            for answer in round_findings["answers"]:
                all_findings["key_insights"].extend(answer.get("key_points", []))
        
        return all_findings
    
    def _make_trading_decision(self, ticker: str, stock_data: Dict, detailed_analysis: Dict) -> Dict:
        """Generate final trading decision based on deep analysis"""
        # Combine all insights for final analysis
        all_insights = []
        for round_data in detailed_analysis["rounds"]:
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
        
        # Generate final trading decision
        decision = self.ai_analyzer.generate_trading_decision(
            ticker=ticker,
            news_analysis={
                "sentiment": max(set(sentiments), key=sentiments.count),
                "confidence": avg_confidence,
                "key_points": detailed_analysis["key_insights"],
                "market_impact": "\n".join(i["market_impact"] for i in all_insights)
            },
            stock_data=stock_data,
            personality=personality
        )
        
        # Save trade if action is buy or sell
        if decision["action"] in ["buy", "sell"]:
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
    
    def _generate_summary(self, ticker: str, trading_decision: Dict, detailed_analysis: Dict) -> Dict:
        """Generate single stock analysis summary"""
        return {
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