from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
from sector_mode import SectorMode
from single_stock_mode import SingleStockMode
from web_scraper import WebScraper
import json

class GeneralMode:
    def __init__(self):
        print("\n=== Initializing General Market Mode ===")
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
        self.sector_mode = SectorMode()
        self.single_stock_mode = SingleStockMode()
        self.web_scraper = WebScraper()
        print("✅ General Market Mode initialized")
    
    def run(self) -> Dict:
        """Run general mode trading analysis with enhanced flow"""
        try:
            print("\n🌎 Starting General Market Analysis")
            
            # Step 1: Get and analyze recent market news
            print("\n📰 Fetching today's market news...")
            news_urls = self.news_searcher.search_market_news("today's stock market news last 24 hours")
            print(f"Found {len(news_urls)} news articles")
            
            # Step 2: Scrape and analyze each news article
            print("\n🔍 Scraping and analyzing news articles...")
            market_news = []
            for url_data in news_urls:
                url = url_data.get('url')
                if url:
                    print(f"\n📄 Scraping article from: {url}")
                    scraped_data = self.web_scraper.scrape_and_analyze(url)
                    if scraped_data["success"]:
                        market_news.append(scraped_data)
                        self._save_news(scraped_data)
            
            print(f"\n✅ Successfully scraped {len(market_news)} articles")
            
            # Step 3: Deep analysis of market news
            print("\n🔍 Starting deep market analysis...")
            market_analysis = self._deep_market_analysis(market_news)
            
            # Step 4: Identify sectors and initial tickers from analysis
            print("\n🎯 Identifying key sectors and stocks...")
            sectors, initial_tickers = self._extract_sectors_and_tickers(market_analysis)
            print(f"Identified {len(sectors)} sectors and {len(initial_tickers)} initial tickers")
            
            # Save initial tickers to watchlist
            print("\n💾 Saving initial tickers to watchlist...")
            self.db.update_watchlist(initial_tickers, "GENERAL_MARKET")
            
            # Step 5: Analyze each sector to get more tickers
            print("\n🏢 Analyzing identified sectors...")
            sector_results = []
            all_sector_tickers = set()
            for sector in sectors:
                print(f"\n📊 Analyzing {sector} sector...")
                sector_result = self.sector_mode.run(sector)
                if sector_result["success"]:
                    sector_results.append(sector_result)
                    # Add sector's tickers to our set
                    all_sector_tickers.update(sector_result["stocks_analyzed"])
            
            # Save sector tickers to watchlist
            print("\n💾 Saving sector tickers to watchlist...")
            self.db.update_watchlist(list(all_sector_tickers), "SECTOR_ANALYSIS")
            
            # Step 6: Get complete watchlist and analyze each stock
            print("\n📈 Getting complete watchlist for stock analysis...")
            watchlist = self.db.get_watchlist()  # Get all tickers from watchlist
            print(f"Total tickers in watchlist: {len(watchlist)}")
            
            # Step 7: Analyze each stock in watchlist
            print("\n🔍 Performing deep stock analysis on watchlist...")
            stock_results = []
            for ticker in watchlist:
                print(f"\n🔍 Deep analysis of {ticker}...")
                stock_result = self.single_stock_mode.run(ticker)
                if stock_result["success"]:
                    stock_results.append(stock_result)
                    # Save trade data to database
                    if "trading_decision" in stock_result:
                        self.db.save_trade(
                            ticker=ticker,
                            **stock_result["trading_decision"]
                        )
            
            # Step 8: Generate comprehensive summary
            print("\n📝 Generating comprehensive summary...")
            summary = self._generate_summary(market_analysis, sector_results, stock_results)
            
            # Save final results
            print("\n💾 Saving results to database...")
            self.db.save_summary("general", stock_results, summary)
            
            return {
                "success": True,
                "market_analysis": market_analysis,
                "sectors_analyzed": sectors,
                "stocks_analyzed": watchlist,
                "sector_results": sector_results,
                "stock_results": stock_results,
                "summary": summary
            }
            
        except Exception as e:
            print(f"\n❌ Error in general mode: {str(e)}")
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news_data: Dict) -> None:
        """Save news to database with enhanced metadata"""
        try:
            article = {
                "content": news_data.get("content", ""),
                "url": news_data.get("url", ""),
                "source": news_data.get("metadata", {}).get("source", "unknown"),
                "timestamp": news_data.get("metadata", {}).get("timestamp", str(datetime.now())),
                "content_length": news_data.get("metadata", {}).get("content_length", 0)
            }
            self.db.save_news("MARKET", article, article["source"])
            print(f"✅ Saved article from {article['source']} to database")
        except Exception as e:
            print(f"⚠️ Error saving news: {str(e)}")
    
    def _deep_market_analysis(self, market_news: List[Dict]) -> Dict:
        """Perform deep analysis of market news with follow-up questions"""
        print("\n=== Starting Deep Market Analysis ===")
        
        all_findings = {
            "rounds": [],
            "key_insights": [],
            "market_trends": [],
            "identified_opportunities": [],
            "mentioned_tickers": {}  # Using dict to store tickers by sector
        }
        
        # Initial analysis of market news
        print("\n1️⃣ Analyzing initial market news...")
        
        # Process raw content through LLM first
        processed_articles = []
        for article in market_news:
            if article.get("success", False) and article.get("content"):
                # Create prompt for initial content processing
                process_prompt = f"""Analyze this financial news article and extract key information:

Content:
{article.get('content')}

Source: {article.get('metadata', {}).get('source', 'unknown')}
URL: {article.get('url', '')}

Please provide a structured analysis with the following information:
- A brief 2-3 sentence summary
- Sentiment (bullish/bearish/neutral)
- Confidence score (0-100)
- Key points as bullet points
- Potential market impact
- Any stock tickers mentioned with their sectors (only valid stock symbols, 1-5 capital letters)
- Sector implications

Format your response as valid JSON like this:
{{
    "summary": "your summary here",
    "sentiment": "bullish/bearish/neutral",
    "confidence": 85,
    "key_points": [
        "point 1",
        "point 2"
    ],
    "market_impact": "description here",
    "mentioned_tickers": [
        {{"ticker": "AAPL", "sector": "TECHNOLOGY"}},
        {{"ticker": "MSFT", "sector": "TECHNOLOGY"}}
    ],
    "sector_implications": [
        "implication 1",
        "implication 2"
    ]
}}"""
                
                try:
                    # Process through LLM
                    processed_content = self.ai_analyzer._generate_response(process_prompt)
                    # Clean up any potential trailing commas in JSON
                    processed_content = processed_content.replace(",}", "}")
                    processed_content = processed_content.replace(",]", "]")
                    processed_data = json.loads(processed_content)
                    
                    # Add source metadata
                    processed_data["source"] = article.get("metadata", {}).get("source", "unknown")
                    processed_data["url"] = article.get("url", "")
                    
                    # Collect tickers with their sectors
                    if "mentioned_tickers" in processed_data:
                        for ticker_info in processed_data["mentioned_tickers"]:
                            ticker = ticker_info.get("ticker")
                            sector = ticker_info.get("sector", "UNKNOWN")
                            
                            print(f"Validating ticker: {ticker} (Sector: {sector})")
                            try:
                                data = self.stock_data.get_stock_data(ticker, period="1d")
                                if data["success"]:
                                    print(f"✅ Valid ticker found: {ticker}")
                                    # Initialize sector in dict if not exists
                                    if sector not in all_findings["mentioned_tickers"]:
                                        all_findings["mentioned_tickers"][sector] = set()
                                    # Add ticker to its sector
                                    all_findings["mentioned_tickers"][sector].add(ticker)
                                else:
                                    print(f"❌ Invalid ticker: {ticker}")
                            except Exception as e:
                                print(f"⚠️ Error validating ticker {ticker}: {str(e)}")
                    
                    processed_articles.append(processed_data)
                    print(f"\n✅ Processed article from {processed_data['source']}")
                    print(f"📊 Sentiment: {processed_data['sentiment']} ({processed_data['confidence']}% confidence)")
                    print(f"📝 Key Points: {len(processed_data['key_points'])}")
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON parsing error: {str(e)}")
                    print("Raw content:", processed_content)
                    continue
                except Exception as e:
                    print(f"⚠️ Error processing article: {str(e)}")
                    continue
        
        print(f"\n📊 Successfully processed {len(processed_articles)} articles")
        
        # Save validated tickers to watchlist by sector
        if all_findings["mentioned_tickers"]:
            print("\n💾 Saving validated tickers to watchlist by sector...")
            for sector, tickers in all_findings["mentioned_tickers"].items():
                if tickers:  # Only save if there are tickers for this sector
                    print(f"Saving {len(tickers)} tickers for sector: {sector}")
                    self.db.update_watchlist(list(tickers), sector)
        
        # Convert sets to lists for JSON serialization
        all_findings["mentioned_tickers"] = {
            sector: list(tickers) 
            for sector, tickers in all_findings["mentioned_tickers"].items()
        }
        
        # Now analyze the processed articles
        initial_analysis = self.ai_analyzer.analyze_news(processed_articles)
        current_summary = f"""
        Market Impact: {initial_analysis.get('market_impact', '')}
        Sentiment: {initial_analysis.get('sentiment', 'neutral')}
        Key Points: {', '.join(initial_analysis.get('key_points', []))}
        Market Trends: {', '.join(initial_analysis.get('market_trends', []))}
        """
        
        # Multiple rounds of follow-up questions
        for round_num in range(2):
            print(f"\n🔄 Analysis Round {round_num + 1}")
            round_findings = {
                "questions": [],
                "answers": [],
                "tools_used": []
            }
            
            # Generate market-focused questions
            questions = self.ai_analyzer.generate_follow_up_questions("MARKET", current_summary)
            print(f"Generated {len(questions)} follow-up questions")
            
            for i, q in enumerate(questions):
                print(f"\n❓ Question {i+1}: {q.get('text', '')}")
                
                # Search for specific answers
                new_urls = self.news_searcher.search_market_news(q.get('text', ''))
                new_articles = []
                
                # Scrape and process new articles
                for url_data in new_urls:
                    url = url_data.get('url')
                    if url:
                        try:
                            scraped_data = self.web_scraper.scrape_and_analyze(url)
                            if scraped_data["success"] and scraped_data.get("content"):
                                # Process through LLM
                                process_prompt = f"""Analyze this financial news article and extract key information:

Content:
{scraped_data.get('content')}

Source: {scraped_data.get('metadata', {}).get('source', 'unknown')}
URL: {url}

Please provide a structured analysis in the following format:
{{
    "summary": "Brief 2-3 sentence summary of the article",
    "sentiment": "bullish/bearish/neutral",
    "confidence": "0-100 score indicating sentiment strength",
    "key_points": ["List of key points as bullet points"],
    "market_impact": "Description of potential market impact",
    "mentioned_tickers": ["Any stock tickers mentioned"],
    "sector_implications": ["Any sector-wide implications"]
}}"""
                                
                                processed_content = self.ai_analyzer._generate_response(process_prompt)
                                processed_data = json.loads(processed_content)
                                processed_data["source"] = scraped_data.get("metadata", {}).get("source", "unknown")
                                processed_data["url"] = url
                                
                                new_articles.append(processed_data)
                                self._save_news(scraped_data)
                                
                                print(f"✅ Processed article from {processed_data['source']}")
                                print(f"📊 Sentiment: {processed_data['sentiment']} ({processed_data['confidence']}% confidence)")
                                print(f"📝 Key Points: {len(processed_data['key_points'])}")
                                
                        except Exception as e:
                            print(f"⚠️ Error processing article: {str(e)}")
                            continue
                
                # Analyze findings
                analysis = self.ai_analyzer.analyze_news(new_articles)
                print(f"Round {round_num + 1} Question {i+1} Analysis:")
                print(f"Sentiment: {analysis.get('sentiment', 'unknown')}")
                print(f"Key Points: {len(analysis.get('key_points', []))}")
                
                round_findings["questions"].append(q)
                round_findings["answers"].append(analysis)
                
                # Update context for next questions
                if analysis and isinstance(analysis, dict):
                    new_context = f"""
                    New Analysis:
                    Market Impact: {analysis.get('market_impact', '')}
                    Sentiment: {analysis.get('sentiment', 'neutral')}
                    Key Points: {', '.join(analysis.get('key_points', []))}
                    Market Trends: {', '.join(analysis.get('market_trends', []))}
                    """
                    current_summary += "\n" + new_context
            
            all_findings["rounds"].append(round_findings)
            
            # Extract insights from this round
            for answer in round_findings["answers"]:
                if isinstance(answer, dict):
                    all_findings["key_insights"].extend(answer.get("key_points", []))
                    if "market_trends" in answer:
                        all_findings["market_trends"].extend(answer["market_trends"])
                    if "opportunities" in answer:
                        all_findings["identified_opportunities"].extend(answer["opportunities"])
        
        return all_findings
    
    def _extract_sectors_and_tickers(self, market_analysis: Dict) -> tuple[List[str], List[str]]:
        """Extract relevant sectors and tickers from market analysis"""
        print("\n=== Extracting Sectors and Tickers ===")
        
        # Create a prompt for sector and ticker extraction
        prompt = f"""Analyze this market analysis and identify:
1. Key market sectors that are showing significant activity or opportunities
2. Specific stock tickers mentioned or implied
3. Rank both sectors and tickers by relevance and potential

Market Analysis:
{json.dumps(market_analysis, indent=2)}

Provide analysis in JSON format:
{{
    "sectors": [
        {{"name": "sector_name", "relevance": "high/medium/low", "reason": "reason for inclusion"}}
    ],
    "tickers": [
        {{"symbol": "TICK", "sector": "sector_name", "relevance": "high/medium/low"}}
    ]
}}"""

        # Get AI response
        try:
            response = self.ai_analyzer._generate_response(prompt)
            analysis = json.loads(response)
            
            # Extract and validate sectors
            sectors = []
            for sector_info in analysis.get("sectors", []):
                if sector_info.get("relevance", "").lower() in ["high", "medium"]:
                    sectors.append(sector_info["name"])
            
            # Extract and validate tickers
            tickers = []
            for ticker_info in analysis.get("tickers", []):
                ticker = ticker_info.get("symbol", "")
                if ticker_info.get("relevance", "").lower() in ["high", "medium"]:
                    print(f"\nValidating {ticker}...")
                    data = self.stock_data.get_stock_data(ticker, period="1d")
                    if data["success"]:
                        print(f"✓ {ticker} is valid")
                        tickers.append(ticker)
                    else:
                        print(f"✗ {ticker} is invalid")
            
            return sectors[:5], tickers  # Limit to top 5 sectors
            
        except Exception as e:
            print(f"Error extracting sectors and tickers: {str(e)}")
            return [], []
    
    def _generate_summary(self, market_analysis: Dict, sector_results: List[Dict], stock_results: List[Dict]) -> Dict:
        """Generate comprehensive trading summary"""
        print("\n=== Generating Comprehensive Summary ===")
        
        # Aggregate trading decisions
        all_decisions = []
        for result in stock_results:
            if "trading_decision" in result:
                print(f"Processing trading decision: {result['trading_decision']}")
                all_decisions.append(result["trading_decision"])
            else:
                print(f"Warning: No trading decision found in result: {result.keys()}")
        
        print(f"Total decisions collected: {len(all_decisions)}")
        
        buy_decisions = [d for d in all_decisions if d.get("recommendation", "").lower() == "buy"]
        sell_decisions = [d for d in all_decisions if d.get("recommendation", "").lower() == "sell"]
        hold_decisions = [d for d in all_decisions if d.get("recommendation", "").lower() == "hold"]
        
        print(f"Buy decisions: {len(buy_decisions)}")
        print(f"Sell decisions: {len(sell_decisions)}")
        print(f"Hold decisions: {len(hold_decisions)}")
        
        # Calculate sector performance
        sector_insights = []
        for sector_result in sector_results:
            if sector_result.get("success"):
                sector_insights.append({
                    "sector": sector_result["sector"],
                    "sentiment": sector_result["summary"]["sector_sentiment"],
                    "confidence": sector_result["summary"]["sector_confidence"],
                    "stocks_analyzed": len(sector_result["stocks_analyzed"])
                })
        
        return {
            "timestamp": str(datetime.now()),
            "market_sentiment": market_analysis.get("sentiment", "neutral"),
            "market_confidence": market_analysis.get("confidence", 0),
            "key_market_insights": market_analysis.get("key_insights", []),
            "market_trends": market_analysis.get("market_trends", []),
            "sectors_analyzed": len(sector_results),
            "sector_insights": sector_insights,
            "total_stocks_analyzed": len(stock_results),
            "trading_decisions": {
                "total": len(all_decisions),
                "buy": len(buy_decisions),
                "sell": len(sell_decisions),
                "hold": len(hold_decisions)
            },
            "average_confidence": sum(d["confidence"] for d in all_decisions) / len(all_decisions) if all_decisions else 0
        } 