import requests
import json
from typing import Dict, List, Tuple, Any
from config import OLLAMA_URL, OLLAMA_MODEL
import time
from datetime import datetime
import re

class AIAnalyzer:
    def __init__(self):
        print("\n=== Initializing AI Analyzer ===")
        self.base_url = OLLAMA_URL
        self.model = OLLAMA_MODEL
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        # Initialize ChromaDB handler
        try:
            from chromadb_handler import ChromaDBHandler
            self.chroma_handler = ChromaDBHandler()
            print("✅ ChromaDB handler initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize ChromaDB handler: {str(e)}")
            self.chroma_handler = None
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response from Ollama"""
        try:
            print("\n🤖 Generating AI response...")
            print("📤 Sending prompt to Ollama...")
            
            # Clean prompt to use single curly braces
            prompt = prompt.replace("{{", "{").replace("}}", "}")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers=self.headers,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60  # Add timeout
            )
            
            print(f"📥 Response status code: {response.status_code}")
            
            response.raise_for_status()
            result = response.json().get("response", "")
            
            if not result:
                print("⚠️ Empty response received")
                return ""
                
            # Clean response JSON
            result = result.replace("{{", "{").replace("}}", "}")
            result = result.strip()
            
            # Fix common JSON formatting issues
            result = re.sub(r',(\s*[}\]])', r'\1', result)  # Remove trailing commas
            result = re.sub(r'}\s*{', '},{', result)  # Fix object separators
            result = re.sub(r']\s*\[', '],[', result)  # Fix array separators
            result = re.sub(r'(["\'])\s*\n\s*(["\'])', r'\1,\2', result)  # Add missing commas between strings
            result = re.sub(r'(["\'])\s*(["\'])', r'\1,\2', result)  # Add missing commas between strings
            
            # Fix array elements missing commas
            result = re.sub(r'(["\']\s*})\s*(\s*["\'])', r'\1,\2', result)  # Add missing commas between array elements
            result = re.sub(r'(})\s*({)', r'},\1', result)  # Add missing commas between objects
            
            # Validate JSON structure
            try:
                parsed_json = json.loads(result)
                result = json.dumps(parsed_json, indent=4)  # Reformat with proper indentation
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error: {str(e)}")
                print("Raw content:", result)
                
                # Additional cleanup for specific cases
                if '"key_points": [' in result:
                    # Fix missing commas in arrays
                    pattern = r'(\s*"[^"]+"\s*)\s+(\s*")'
                    result = re.sub(pattern, r'\1,\2', result)
                
                # Try parsing again after additional cleanup
                try:
                    parsed_json = json.loads(result)
                    result = json.dumps(parsed_json, indent=4)
                except json.JSONDecodeError:
                    print("⚠️ Failed to fix JSON structure")
                    return ""
            
            print(f"📥 Response: {result}")
            return result
            
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
            return ""
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {str(e)}")
            return ""
        except Exception as e:
            print(f"❌ Error generating response: {str(e)}")
            return ""
    
    def _print_analysis_step(self, step_num: int, step_name: str, data: Dict) -> None:
        """Helper to print analysis steps in a structured way"""
        print(f"\n=== Step {step_num}: {step_name} ===")
        for key, value in data.items():
            if isinstance(value, list):
                print(f"\n{key.replace('_', ' ').title()}:")
                for item in value:
                    print(f"  • {item}")
            else:
                print(f"\n{key.replace('_', ' ').title()}: {value}")
    
    def analyze_news(self, news_data: List[Dict]) -> Dict:
        """Analyze news data using chain-of-thought reasoning"""
        print("\n🔍 Starting Chain-of-Thought News Analysis...")
        print(f"📰 Analyzing {len(news_data)} news articles")
        
        # Add debugging for news data
        for i, article in enumerate(news_data):
            print(f"\nArticle {i+1}:")
            print(f"Summary: {article.get('summary', 'No summary')[:100]}...")
            print(f"Sentiment: {article.get('sentiment', 'No sentiment')}")
            print(f"Key points: {len(article.get('key_points', []))} points")
        
        # Break down analysis into smaller chunks if too many articles
        chunk_size = 3
        if len(news_data) > chunk_size:
            print(f"\n📦 Breaking analysis into chunks of {chunk_size} articles...")
            chunks = [news_data[i:i + chunk_size] for i in range(0, len(news_data), chunk_size)]
            
            all_analyses = []
            for i, chunk in enumerate(chunks):
                print(f"\n🔄 Analyzing chunk {i+1}/{len(chunks)}...")
                chunk_analysis = self._analyze_news_chunk(chunk)
                if chunk_analysis:
                    all_analyses.append(chunk_analysis)
            
            # Combine chunk analyses
            return self._combine_analyses(all_analyses)
        else:
            # Analyze single chunk
            return self._analyze_news_chunk(news_data)
    
    def _analyze_news_chunk(self, news_chunk: List[Dict]) -> Dict:
        """Analyze a smaller chunk of news articles"""
        max_retries = 3
        
        # Create prompt for chunk analysis
        prompt = f"""Analyze these news articles and provide a structured analysis:

News Articles:
{json.dumps(news_chunk, indent=2)}

Provide analysis in this exact JSON format:
{{
    "summaries": [
        "summary 1",
        "summary 2"
    ],
    "themes": [
        "theme 1",
        "theme 2"
    ],
    "sentiment": "bullish/bearish/neutral",
    "confidence": 0-100,
    "key_points": [
        "point 1",
        "point 2"
    ],
    "market_impact": "description",
    "reasoning": {{
        "bullish_factors": [
            "factor 1",
            "factor 2"
        ],
        "bearish_factors": [
            "factor 1",
            "factor 2"
        ],
        "conclusion": "detailed conclusion"
    }}
}}"""

        for attempt in range(max_retries):
            try:
                response = self._generate_response(prompt)
                if not response:
                    print(f"⚠️ Empty response on attempt {attempt + 1}")
                    continue
                    
                # Clean the response
                response = response.strip()
                response = re.sub(r',(\s*[}\]])', r'\1', response)  # Remove trailing commas
                response = re.sub(r'}\s*{', '},{', response)  # Fix object separators
                response = re.sub(r']\s*\[', '],[', response)  # Fix array separators
                
                analysis = json.loads(response)
                
                # Validate analysis structure
                required_fields = ['summaries', 'themes', 'sentiment', 'confidence', 'key_points', 'market_impact', 'reasoning']
                missing_fields = [field for field in required_fields if field not in analysis]
                
                if missing_fields:
                    print(f"⚠️ Missing fields in analysis: {missing_fields}")
                    # Add default values for missing fields
                    for field in missing_fields:
                        if field == 'sentiment':
                            analysis[field] = 'neutral'
                        elif field == 'confidence':
                            analysis[field] = 0
                        elif field in ['summaries', 'themes', 'key_points']:
                            analysis[field] = []
                        elif field == 'market_impact':
                            analysis[field] = "No market impact analysis available"
                        elif field == 'reasoning':
                            analysis[field] = {
                                "bullish_factors": [],
                                "bearish_factors": [],
                                "conclusion": "No detailed conclusion available"
                            }
                
                # Ensure arrays have proper commas
                for field in ['summaries', 'themes', 'key_points']:
                    if isinstance(analysis.get(field), list):
                        analysis[field] = [str(item).strip() for item in analysis[field] if item]
                
                # Print detailed analysis steps
                print("\n📰 News Analysis Process:")
                self._print_analysis_step(1, "Article Summaries", {"summaries": analysis.get("summaries", [])})
                self._print_analysis_step(2, "Common Themes", {"themes": analysis.get("themes", [])})
                self._print_analysis_step(3, "Market Impact Analysis", {
                    "sentiment": analysis.get("sentiment", "neutral"),
                    "confidence": f"{analysis.get('confidence', 0)}%",
                    "market_impact": analysis.get("market_impact", "")
                })
                self._print_analysis_step(4, "Bullish vs Bearish Analysis", {
                    "bullish_factors": analysis.get("reasoning", {}).get("bullish_factors", []),
                    "bearish_factors": analysis.get("reasoning", {}).get("bearish_factors", [])
                })
                self._print_analysis_step(5, "Final Conclusion", {
                    "conclusion": analysis.get("reasoning", {}).get("conclusion", ""),
                    "key_points": analysis.get("key_points", [])
                })
                
                return analysis
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse AI response on attempt {attempt + 1}: {str(e)}")
                print("Raw response:", response[:500])
                if attempt == max_retries - 1:
                    return self._get_default_analysis()
                time.sleep(2)  # Wait before retrying
                
            except Exception as e:
                print(f"❌ Error in analysis on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries - 1:
                    return self._get_default_analysis()
                time.sleep(2)  # Wait before retrying
    
    def _save_to_chroma(self, analysis: Dict, metadata: Dict) -> bool:
        """Helper method to save analysis to ChromaDB"""
        if not self.chroma_handler:
            print("⚠️ ChromaDB handler not available, skipping save")
            return False
            
        try:
            print("\n💾 Saving analysis to ChromaDB...")
            success = self.chroma_handler.save_document(
                collection_name="summary",
                document=json.dumps(analysis, indent=4),
                metadata=metadata
            )
            if success:
                print("✅ Analysis saved to ChromaDB")
            return success
        except Exception as e:
            print(f"⚠️ Failed to save to ChromaDB: {str(e)}")
            return False
    
    def _combine_analyses(self, analyses: List[Dict]) -> Dict:
        """Combine multiple chunk analyses into a single analysis"""
        if not analyses:
            return self._get_default_analysis()
            
        print("\n🔄 Combining chunk analyses...")
        
        # Combine all summaries and themes
        all_summaries = []
        all_themes = []
        all_key_points = []
        all_bullish = []
        all_bearish = []
        
        # Track sentiment counts and total confidence
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        total_confidence = 0
        
        for analysis in analyses:
            all_summaries.extend(analysis.get("summaries", []))
            all_themes.extend(analysis.get("themes", []))
            all_key_points.extend(analysis.get("key_points", []))
            all_bullish.extend(analysis.get("reasoning", {}).get("bullish_factors", []))
            all_bearish.extend(analysis.get("reasoning", {}).get("bearish_factors", []))
            
            sentiment = analysis.get("sentiment", "neutral")
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            total_confidence += analysis.get("confidence", 0)
        
        # Calculate overall sentiment and confidence
        overall_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
        avg_confidence = total_confidence / len(analyses)
        
        # Deduplicate lists while preserving order
        all_summaries = list(dict.fromkeys(all_summaries))
        all_themes = list(dict.fromkeys(all_themes))
        all_key_points = list(dict.fromkeys(all_key_points))
        all_bullish = list(dict.fromkeys(all_bullish))
        all_bearish = list(dict.fromkeys(all_bearish))
        
        # Generate combined market impact and conclusion with enforced JSON structure
        impact_prompt = f"""Synthesize these analyses into a market impact statement:

Themes: {json.dumps(all_themes)}
Key Points: {json.dumps(all_key_points)}
Overall Sentiment: {overall_sentiment}
Confidence: {avg_confidence}%

Format response as JSON:
{{
    "market_impact": "your concise market impact analysis here"
}}"""
        
        conclusion_prompt = f"""Create a detailed conclusion based on these factors:

Bullish Factors: {json.dumps(all_bullish)}
Bearish Factors: {json.dumps(all_bearish)}
Overall Sentiment: {overall_sentiment}
Confidence: {avg_confidence}%

Format response as JSON:
{{
    "conclusion": "your thorough conclusion here",
    "sentiment": "{overall_sentiment}",
    "confidence": {avg_confidence},
    "bullish_summary": "summary of bullish factors",
    "bearish_summary": "summary of bearish factors"
}}"""
        
        try:
            impact_response = json.loads(self._generate_response(impact_prompt))
            conclusion_response = json.loads(self._generate_response(conclusion_prompt))
            
            combined_impact = impact_response.get("market_impact", "No market impact available")
            combined_conclusion = conclusion_response.get("conclusion", "No conclusion available")
            
        except json.JSONDecodeError:
            print("⚠️ Error parsing impact/conclusion JSON, using defaults")
            combined_impact = "Error generating market impact"
            combined_conclusion = "Error generating conclusion"
        
        combined_analysis = {
            "summaries": all_summaries,
            "themes": all_themes,
            "sentiment": overall_sentiment,
            "confidence": avg_confidence,
            "key_points": all_key_points,
            "market_impact": combined_impact,
            "reasoning": {
                "bullish_factors": all_bullish,
                "bearish_factors": all_bearish,
                "conclusion": combined_conclusion
            }
        }
        
        # Save to ChromaDB with proper JSON structure
        self._save_to_chroma(
            analysis=combined_analysis,
            metadata={
                "timestamp": str(datetime.now()),
                "num_articles": len(all_summaries),
                "sentiment": overall_sentiment,
                "confidence": avg_confidence
            }
        )
        
        return combined_analysis
    
    def _get_default_analysis(self) -> Dict:
        """Return default analysis structure when errors occur"""
        return {
            "sentiment": "neutral",
            "confidence": 0,
            "summaries": [],
            "themes": [],
            "key_points": [],
            "market_impact": "Error analyzing news",
            "reasoning": {
                "bullish_factors": [],
                "bearish_factors": [],
                "conclusion": "Failed to analyze news data"
            }
        }
    
    def generate_trading_decision(self, 
                                ticker: str,
                                news_analysis: Dict,
                                stock_data: Dict,
                                personality: str) -> Dict:
        """Generate trading decision using graph-of-thought reasoning"""
        print(f"\n🎯 Starting Graph-of-Thought Trading Analysis for {ticker}...")
        print(f"\nTrading Personality: {personality}")
        print(f"Current Price: ${stock_data.get('current_price', 0):.2f}")
        print(f"Daily Change: {stock_data.get('daily_change', 0):.2f}%")
        
        prompt = f"""As a {personality} trader, analyze the following data using graph-of-thought reasoning to make a trading decision:

Ticker: {ticker}
News Analysis: {json.dumps(news_analysis, indent=2)}
Stock Data: {json.dumps(stock_data, indent=2)}

Follow this decision-making process:

1. Build a graph of interconnected factors:
   - Technical indicators
   - News sentiment
   - Market conditions
   - Risk factors
   - Trading psychology
   - Price trends

2. Analyze relationships between factors:
   - How do they influence each other?
   - What are the key dependencies?
   - Which factors have the most impact?

3. Consider multiple scenarios:
   - Best case
   - Worst case
   - Most likely case

4. Apply {personality} trading style:
   - Risk tolerance
   - Time horizon
   - Decision criteria

5. Make a final decision based on the complete analysis.

Provide your decision in JSON format with the following structure:
{{
    "action": "buy/sell/hold",
    "confidence": 0-100,
    "quantity": "number of shares",
    "entry_price": "suggested entry price",
    "stop_loss": "suggested stop loss price",
    "take_profit": "suggested take profit price",
    "reasoning": {{
        "technical_factors": ["factor1", "factor2", "..."],
        "fundamental_factors": ["factor1", "factor2", "..."],
        "risk_factors": ["factor1", "factor2", "..."],
        "decision_process": "detailed explanation"
    }},
    "scenarios": {{
        "best_case": "description",
        "worst_case": "description",
        "most_likely": "description"
    }},
    "risk_assessment": {{
        "risk_level": "low/medium/high",
        "key_risks": ["risk1", "risk2", "..."],
        "mitigation_strategies": ["strategy1", "strategy2", "..."]
    }}
}}"""
        
        response = self._generate_response(prompt)
        try:
            decision = json.loads(response)
            
            # Print detailed decision process
            print("\n📊 Trading Decision Process:")
            
            self._print_analysis_step(1, "Technical Analysis", {
                "technical_factors": decision.get("reasoning", {}).get("technical_factors", [])
            })
            
            self._print_analysis_step(2, "Fundamental Analysis", {
                "fundamental_factors": decision.get("reasoning", {}).get("fundamental_factors", [])
            })
            
            self._print_analysis_step(3, "Scenario Analysis", decision.get("scenarios", {
                "best_case": "Not available",
                "worst_case": "Not available",
                "most_likely": "Not available"
            }))
            
            self._print_analysis_step(4, "Risk Assessment", {
                "risk_level": decision.get("risk_assessment", {}).get("risk_level", "unknown"),
                "key_risks": decision.get("risk_assessment", {}).get("key_risks", []),
                "mitigation_strategies": decision.get("risk_assessment", {}).get("mitigation_strategies", [])
            })
            
            self._print_analysis_step(5, "Final Decision", {
                "action": decision.get("action", "hold").upper(),
                "confidence": f"{decision.get('confidence', 0)}%",
                "quantity": decision.get("quantity", 0),
                "entry_price": f"${decision.get('entry_price', 0)}",
                "stop_loss": f"${decision.get('stop_loss', 0)}",
                "take_profit": f"${decision.get('take_profit', 0)}",
                "decision_process": decision.get("reasoning", {}).get("decision_process", "")
            })
            
            return decision
        except:
            return {
                "action": "hold",
                "confidence": 0,
                "quantity": 0,
                "entry_price": 0,
                "stop_loss": 0,
                "take_profit": 0,
                "reasoning": "Error generating decision",
                "risk_assessment": "Error assessing risk"
            }
    
    def analyze_content(self, scraped_data: Dict) -> Dict:
        """Analyze scraped content"""
        if not scraped_data.get("success"):
            return scraped_data
            
        try:
            content = scraped_data["content"]
            source = scraped_data["metadata"]["source"]
            
            prompt = f"""Analyze this {source} content and provide:
            1. A concise summary focused on market impact
            2. The sentiment (bullish/bearish/neutral) with explanation
            3. Three key insights that could affect trading decisions
            
            Content: {content[:3000]}
            
            Respond in JSON format:
            {{
                "summary": "...",
                "sentiment": {{
                    "direction": "bullish/bearish/neutral",
                    "explanation": "..."
                }},
                "key_points": [
                    "point 1",
                    "point 2",
                    "point 3"
                ],
                "market_impact": "..."
            }}"""
            
            analysis = json.loads(self._generate_response(prompt))
            return {
                "success": True,
                "summary": analysis["summary"],
                "sentiment": analysis["sentiment"],
                "key_points": analysis["key_points"],
                "market_impact": analysis.get("market_impact", "")
            }
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_follow_up_questions(self, ticker: str, current_context: str) -> List[Dict]:
        """Generate targeted follow-up questions for a specific ticker"""
        prompt = f"""Based on this context about {ticker}, generate 3 specific follow-up questions.
        
        Context: {current_context}
        
        Requirements:
        1. Each question must be about {ticker} specifically
        2. Focus on recent developments, financials, or competitive position
        3. Questions should help with trading decisions
        
        Respond in JSON format:
        {{
            "questions": [
                {{
                    "text": "What is {ticker}'s...",
                    "tool": "news_search/financial_data/market_analysis",
                    "rationale": "This will help understand..."
                }}
            ]
        }}"""
        
        try:
            response = json.loads(self._generate_response(prompt))
            questions = response.get("questions", [])
            
            # Ensure each question has required fields
            validated_questions = []
            for q in questions:
                if isinstance(q, dict):
                    # Convert old format if needed
                    if "question" in q and "text" not in q:
                        q["text"] = q.pop("question")
                    if "research_tool" in q and "tool" not in q:
                        q["tool"] = q.pop("research_tool")
                    
                    # Validate required fields
                    if "text" in q and "tool" in q and "rationale" in q:
                        validated_questions.append(q)
            
            if not validated_questions:
                return self._get_default_questions(ticker)
                
            return validated_questions
            
        except Exception as e:
            print(f"❌ Error generating questions: {str(e)}")
            return self._get_default_questions(ticker)
    
    def _get_default_questions(self, ticker: str) -> List[Dict]:
        """Return default questions when generation fails"""
        return [
            {
                "text": f"What are {ticker}'s latest quarterly earnings results?",
                "tool": "financial_data",
                "rationale": "Understanding recent financial performance"
            },
            {
                "text": f"What recent news has affected {ticker}'s stock price?",
                "tool": "news_search",
                "rationale": "Identifying price catalysts"
            },
            {
                "text": f"How does {ticker}'s valuation compare to peers?",
                "tool": "market_analysis",
                "rationale": "Assessing relative value"
            }
        ]
    
    def select_trading_personality(self) -> str:
        """Select trading personality based on market conditions using chain-of-thought"""
        print("\n👤 Starting Chain-of-Thought Personality Selection...")
        
        prompt = """Analyze current market conditions and select the most appropriate trading personality.

Think through the following steps:

1. Assess market conditions:
   - Volatility levels
   - Trend strength
   - Sector rotations
   - Risk sentiment

2. Consider trading styles:
   - Conservative: Focus on capital preservation
   - Moderate: Balanced risk/reward
   - Aggressive: High risk/high reward
   - Data-Driven: Quantitative approach
   - News-Focused: Event-driven trading
   - Trend-Following: Momentum-based
   - Counter-Trend: Mean reversion
   - Technical: Chart patterns
   - Fundamental: Value-based

3. Match conditions to personality:
   - Which style is best suited?
   - What are the pros and cons?
   - How would each style perform?

Provide your response in JSON format with:
{
    "personality": "selected personality",
    "market_conditions": ["condition1", "condition2", ...],
    "reasoning": "detailed explanation",
    "expected_performance": "why this personality would work well"
}"""
        
        response = self._generate_response(prompt)
        try:
            result = json.loads(response)
            
            # Print personality selection process
            print("\nPersonality Selection Process:")
            self._print_analysis_step(1, "Market Conditions", {
                "conditions": result.get("market_conditions", [])
            })
            self._print_analysis_step(2, "Selection Reasoning", {
                "personality": result.get("personality", "Moderate"),
                "reasoning": result.get("reasoning", ""),
                "expected_performance": result.get("expected_performance", "")
            })
            
            return result.get("personality", "Moderate")
        except:
            return "Moderate" 