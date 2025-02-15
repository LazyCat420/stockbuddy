from typing import Dict, List
from datetime import datetime
from news_search import NewsSearcher
from ai_analysis import AIAnalyzer
from stock_data import StockDataHandler
from database import DatabaseHandler
from sector_mode import SectorMode
from single_stock_mode import SingleStockMode
from web_scraper import WebScraper
from utils.console_colors import console
import json

class GeneralMode:
    def __init__(self):
        print(f"\n{console.title('=== Initializing General Market Mode ===')}")
        self.news_searcher = NewsSearcher()
        self.ai_analyzer = AIAnalyzer()
        self.stock_data = StockDataHandler()
        self.db = DatabaseHandler()
        self.sector_mode = SectorMode()
        self.single_stock_mode = SingleStockMode()
        self.web_scraper = WebScraper()
        print(f"{console.success('✅ General Market Mode initialized')}")
    
    def run(self) -> Dict:
        """Run general mode trading analysis with enhanced flow"""
        try:
            print(f"\n{console.title('🌎 Starting General Market Analysis')}")
            
            # Step 1: Get and analyze recent market news
            print(f"\n{console.title('📰 Step 1: Fetching today market news...')}")
            news_urls = self.news_searcher.search_market_news("today's stock market news last 24 hours")
            print(f"{console.info(f'Found {console.metric(str(len(news_urls)))} news articles')}")
            
            # Step 2: Scrape and analyze each news article
            print(f"\n{console.title('🔍 Step 2: Scraping and analyzing news articles...')}")
            market_news = []
            for url_data in news_urls:
                url = url_data.get('url')
                if url:
                    try:
                        print(f"\n{console.info(f'📄 Scraping article from: {url}')}")
                        scraped_data = self.web_scraper.scrape_and_analyze(url)
                        
                        if scraped_data["success"]:
                            print(f"\n{console.highlight('📝 Generating article analysis...')}")
                            # Create prompt for content analysis
                            process_prompt = f"""Analyze this financial news article and extract key information:

Content:
{scraped_data.get('content')}

Source: {scraped_data.get('metadata', {}).get('source', 'unknown')}
URL: {url}

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
                            # Get analysis from LLM
                            analysis_content = self.ai_analyzer._generate_response(process_prompt)
                            
                            # Clean up JSON
                            analysis_content = analysis_content.replace(",}", "}")
                            analysis_content = analysis_content.replace(",]", "]")
                            
                            try:
                                analysis_data = json.loads(analysis_content)
                                
                                # Add metadata
                                analysis_data["source"] = scraped_data.get("metadata", {}).get("source", "unknown")
                                analysis_data["url"] = url
                                analysis_data["timestamp"] = str(datetime.now())
                                
                                # Save both scraped content and analysis
                                self._save_news(scraped_data, analysis_data)
                                
                                # Add to market news for further analysis
                                market_news.append({
                                    "content": scraped_data,
                                    "analysis": analysis_data
                                })
                                
                                source = analysis_data["source"]
                                sentiment = analysis_data["sentiment"]
                                confidence = str(analysis_data["confidence"])
                                key_points_count = str(len(analysis_data["key_points"]))
                                
                                print(f"\n{console.success('✅ Successfully processed article from ' + source)}")
                                print(f"{console.info('📊 Sentiment: ' + console.highlight(sentiment) + f' ({console.metric(confidence)}% confidence)')}")
                                print(f"{console.info('📝 Key Points: ' + console.metric(key_points_count))}")
                                
                                if analysis_data.get('mentioned_tickers'):
                                    tickers_str = ', '.join(console.ticker(t['ticker']) for t in analysis_data['mentioned_tickers'])
                                    print(f"{console.info('🎯 Found tickers: ' + tickers_str)}")
                                
                            except json.JSONDecodeError as e:
                                print(f"{console.error('⚠️ JSON parsing error: ' + str(e))}")
                                print(f"{console.warning('Raw content:')} {analysis_content}")
                                continue
                                
                    except Exception as e:
                        print(f"{console.error('⚠️ Error processing article: ' + str(e))}")
                        continue
            
            processed_count = str(len(market_news))
            print(f"\n{console.success('✅ Successfully processed ' + console.metric(processed_count) + ' articles')}")
            
            # Step 3: Deep analysis of market news
            print(f"\n{console.title('🔍 Step 3: Starting deep market analysis...')}")
            market_analysis = self._deep_market_analysis(market_news)
            
            # Step 4: Identify sectors and initial tickers from analysis
            print(f"\n{console.title('🎯 Step 4: Identifying key sectors and stocks...')}")
            sectors, initial_tickers = self._extract_sectors_and_tickers(market_analysis)
            print(f"{console.info(f'Identified {console.metric(str(len(sectors)))} sectors and {console.metric(str(len(initial_tickers)))} initial tickers')}")
            
            # Save initial tickers to watchlist
            print(f"\n{console.title('💾 Step 5: Saving initial tickers to watchlist...')}")
            self.db.update_watchlist(initial_tickers, "GENERAL_MARKET")
            
            # Step 5: Analyze each sector to get more tickers
            print(f"\n{console.title('🏢 Step 6: Analyzing identified sectors...')}")
            sector_results = []
            all_sector_tickers = set()
            for sector in sectors:
                print(f"\n{console.highlight(f'📊 Analyzing {sector} sector...')}")
                sector_result = self.sector_mode.run(sector)
                if sector_result["success"]:
                    sector_results.append(sector_result)
                    all_sector_tickers.update(sector_result["stocks_analyzed"])
            
            # Save sector tickers to watchlist
            print(f"\n{console.title('💾 Step 7: Saving sector tickers to watchlist...')}")
            self.db.update_watchlist(list(all_sector_tickers), "SECTOR_ANALYSIS")
            
            # Step 6: Get complete watchlist and analyze each stock
            print(f"\n{console.title('📈 Step 8: Getting complete watchlist for stock analysis...')}")
            watchlist = self.db.get_watchlist()
            print(f"{console.info(f'Total tickers in watchlist: {console.metric(str(len(watchlist)))}')}")
            
            # Step 7: Analyze each stock in watchlist
            print(f"\n{console.title('🔍 Step 9: Performing deep stock analysis on watchlist...')}")
            stock_results = []
            for ticker in watchlist:
                print(f"\n{console.highlight(f'🔍 Deep analysis of {ticker}...')}")
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
            print(f"\n{console.title('📝 Step 10: Generating comprehensive summary...')}")
            summary = self._generate_summary(market_analysis, sector_results, stock_results)
            
            # Save final results
            print(f"\n{console.title('💾 Step 11: Saving results to database...')}")
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
            print(f"\n{console.error('❌ Error in general mode:')}", str(e))
            import traceback
            print("Traceback:")
            print(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_news(self, news_data: Dict, processed_data: Dict = None) -> None:
        """Save news and its analysis to databases with enhanced metadata"""
        try:
            # Prepare article data with both scraped content and analysis
            article = {
                "content": news_data.get("content", ""),
                "url": news_data.get("url", ""),
                "source": news_data.get("metadata", {}).get("source", "unknown"),
                "timestamp": news_data.get("metadata", {}).get("timestamp", str(datetime.now())),
                "content_length": news_data.get("metadata", {}).get("content_length", 0)
            }
            
            # Add LLM analysis if available
            if processed_data:
                # Validate tickers before adding to analysis
                validated_tickers = []
                if "mentioned_tickers" in processed_data:
                    print(f"\n{console.title('🔍 Validating mentioned tickers...')}")
                    for ticker_info in processed_data["mentioned_tickers"]:
                        ticker = ticker_info.get("ticker")
                        if ticker:
                            try:
                                # Validate with yfinance
                                data = self.stock_data.get_stock_data(ticker, period="1d")
                                if data["success"]:
                                    print(f"{console.success('✅ Valid ticker found: ' + console.ticker(ticker))}")
                                    validated_tickers.append(ticker_info)
                                else:
                                    print(f"{console.error('❌ Invalid ticker: ' + console.ticker(ticker))}")
                            except Exception as e:
                                print(f"{console.error('⚠️ Error validating ticker ' + console.ticker(ticker) + ': ' + str(e))}")
                                continue
                
                # Update processed data with only validated tickers
                processed_data["mentioned_tickers"] = validated_tickers
                
                # Bundle the analysis with the article data
                article.update({
                    "analysis": {
                        "summary": processed_data.get("summary", ""),
                        "sentiment": processed_data.get("sentiment", "neutral"),
                        "confidence": processed_data.get("confidence", 0),
                        "key_points": processed_data.get("key_points", []),
                        "market_impact": processed_data.get("market_impact", ""),
                        "sector_implications": processed_data.get("sector_implications", []),
                        "mentioned_tickers": validated_tickers
                    }
                })
            
            # Save to MongoDB
            source = article["source"]
            self.db.save_news("MARKET", article, source)
            print(f"{console.success('✅ Saved article and analysis from ' + source + ' to MongoDB')}")
            
            # Save to ChromaDB
            if hasattr(self.ai_analyzer, 'chroma_handler') and self.ai_analyzer.chroma_handler:
                chroma_data = {
                    "document": article["content"],
                    "metadata": {
                        "source": article["source"],
                        "url": article["url"],
                        "timestamp": article["timestamp"],
                        "analysis": article.get("analysis", {})
                    }
                }
                self.ai_analyzer.chroma_handler.save_analysis("market_news", chroma_data)
                print(f"{console.success('✅ Saved article and analysis to ChromaDB')}")
                
        except Exception as e:
            print(f"{console.error('⚠️ Error saving news: ' + str(e))}")
            import traceback
            print(f"{console.error('Traceback:')}")
            print(f"{console.error(traceback.format_exc())}")
            
    def _process_and_save_tickers(self, ticker_data: List[Dict]) -> None:
        """Process and save tickers to watchlist with validation"""
        try:
            validated_tickers = {}  # Dict to store tickers by sector
            
            for ticker_info in ticker_data:
                ticker = ticker_info.get("ticker")
                sector = ticker_info.get("sector", "UNKNOWN")
                
                if not ticker:
                    continue
                    
                print(f"Validating ticker: {ticker} (Sector: {sector})")
                try:
                    # Validate with yfinance
                    data = self.stock_data.get_stock_data(ticker, period="1d")
                    if data["success"]:
                        print(f"✅ Valid ticker found: {ticker}")
                        # Initialize sector in dict if not exists
                        if sector not in validated_tickers:
                            validated_tickers[sector] = set()
                        # Add ticker to its sector
                        validated_tickers[sector].add(ticker)
                    else:
                        print(f"❌ Invalid ticker: {ticker}")
                except Exception as e:
                    print(f"⚠️ Error validating ticker {ticker}: {str(e)}")
            
            # Save validated tickers to watchlist by sector
            for sector, tickers in validated_tickers.items():
                if tickers:  # Only save if there are tickers for this sector
                    print(f"Saving {len(tickers)} tickers for sector: {sector}")
                    self.db.update_watchlist(list(tickers), sector)
                    
                    # Save to ChromaDB as well
                    if hasattr(self.ai_analyzer, 'chroma_handler') and self.ai_analyzer.chroma_handler:
                        chroma_data = {
                            "document": f"Sector: {sector}\nTickers: {', '.join(tickers)}",
                            "metadata": {
                                "sector": sector,
                                "tickers": list(tickers),
                                "timestamp": str(datetime.now())
                            }
                        }
                        self.ai_analyzer.chroma_handler.save_analysis("watchlist", chroma_data)
                        print(f"✅ Saved {sector} tickers to ChromaDB watchlist")
                        
        except Exception as e:
            print(f"⚠️ Error processing tickers: {str(e)}")
    
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
                    print(f"\n🔄 Processing article from {article.get('metadata', {}).get('source', 'unknown')}")
                    
                    # Process through LLM
                    processed_content = self.ai_analyzer._generate_response(process_prompt)
                    
                    # Clean up any potential trailing commas in JSON
                    processed_content = processed_content.replace(",}", "}")
                    processed_content = processed_content.replace(",]", "]")
                    
                    try:
                        processed_data = json.loads(processed_content)
                        
                        # Add source metadata
                        processed_data["source"] = article.get("metadata", {}).get("source", "unknown")
                        processed_data["url"] = article.get("url", "")
                        processed_data["timestamp"] = str(datetime.now())
                        
                        # Save both original and processed data
                        self._save_news(article, processed_data)
                        processed_articles.append(processed_data)
                        
                        print(f"✅ Successfully processed article")
                        print(f"📊 Sentiment: {processed_data.get('sentiment')} ({processed_data.get('confidence')}% confidence)")
                        print(f"📝 Key Points: {len(processed_data.get('key_points', []))}")
                        
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parsing error: {str(e)}")
                        print("Raw content:", processed_content)
                        continue
                        
                except Exception as e:
                    print(f"⚠️ Error processing article: {str(e)}")
                    continue
        
        print(f"\n📊 Successfully processed {len(processed_articles)} articles")
        
        # Analyze all processed articles together
        print("\n🔄 Generating combined analysis...")
        combined_analysis = self.ai_analyzer.analyze_news(processed_articles)
        
        # Save combined analysis to database
        try:
            combined_summary = {
                "type": "market_summary",
                "timestamp": str(datetime.now()),
                "analysis": combined_analysis,
                "articles_analyzed": len(processed_articles),
                "key_insights": combined_analysis.get("key_insights", []),
                "market_trends": combined_analysis.get("market_trends", []),
                "overall_sentiment": combined_analysis.get("sentiment", "neutral"),
                "confidence": combined_analysis.get("confidence", 0)
            }
            
            # Save to MongoDB
            self.db.save_summary("market_analysis", combined_summary)
            print("✅ Saved combined analysis to MongoDB")
            
            # Save to ChromaDB
            if hasattr(self.ai_analyzer, 'chroma_handler') and self.ai_analyzer.chroma_handler:
                chroma_data = {
                    "document": json.dumps(combined_analysis, indent=2),
                    "metadata": {
                        "type": "market_summary",
                        "timestamp": str(datetime.now()),
                        "articles_analyzed": len(processed_articles)
                    }
                }
                self.ai_analyzer.chroma_handler.save_analysis("market_summary", chroma_data)
                print("✅ Saved combined analysis to ChromaDB")
                
        except Exception as e:
            print(f"⚠️ Error saving combined analysis: {str(e)}")
        
        return combined_analysis
    
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