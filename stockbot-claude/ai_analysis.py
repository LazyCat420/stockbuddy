import requests
import json
from typing import Dict, List, Tuple, Any
from config import OLLAMA_URL, OLLAMA_MODEL

class AIAnalyzer:
    def __init__(self):
        self.base_url = OLLAMA_URL
        self.model = OLLAMA_MODEL
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response from Ollama"""
        try:
            print("\nGenerating AI response...")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json().get("response", "")
            print("Response received")
            return result
        except Exception as e:
            print(f"Error generating response: {str(e)}")
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
        
        prompt = f"""Analyze the following news articles using step-by-step reasoning:

News articles:
{json.dumps(news_data, indent=2)}

Follow these steps:
1. First, summarize the key information from each article
2. Then, identify common themes and patterns
3. Next, analyze potential market impacts
4. Consider both bullish and bearish arguments
5. Finally, synthesize all information into a conclusion

Think through each step carefully and explain your reasoning.

Provide your analysis in JSON format with the following structure:
{{
    "summaries": ["summary1", "summary2", ...],
    "themes": ["theme1", "theme2", ...],
    "sentiment": "bullish/bearish/neutral",
    "confidence": 0-100,
    "key_points": ["point1", "point2", ...],
    "market_impact": "description",
    "reasoning": {{
        "bullish_factors": ["factor1", "factor2", ...],
        "bearish_factors": ["factor1", "factor2", ...],
        "conclusion": "detailed explanation"
    }}
}}"""
        
        response = self._generate_response(prompt)
        try:
            analysis = json.loads(response)
            
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
        except:
            return {
                "sentiment": "neutral",
                "confidence": 0,
                "key_points": [],
                "market_impact": "Error analyzing news",
                "reasoning": "Failed to parse AI response"
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
        "technical_factors": ["factor1", "factor2", ...],
        "fundamental_factors": ["factor1", "factor2", ...],
        "risk_factors": ["factor1", "factor2", ...],
        "decision_process": "detailed explanation"
    }},
    "scenarios": {{
        "best_case": "description",
        "worst_case": "description",
        "most_likely": "description"
    }},
    "risk_assessment": {{
        "risk_level": "low/medium/high",
        "key_risks": ["risk1", "risk2", ...],
        "mitigation_strategies": ["strategy1", "strategy2", ...]
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
    
    def generate_follow_up_questions(self, ticker: str, news_summary: str) -> List[str]:
        """Generate follow-up questions using tree-of-thought reasoning"""
        print(f"\n🌳 Starting Tree-of-Thought Question Generation for {ticker}...")
        
        prompt = f"""Based on the following summary about {ticker}:

{news_summary}

Use tree-of-thought reasoning to generate insightful follow-up questions:

1. Start with broad areas of investigation:
   - Company fundamentals
   - Market conditions
   - Industry trends
   - Risk factors
   - Growth opportunities

2. For each area:
   - Consider what information is missing
   - Think about potential implications
   - Identify critical uncertainties

3. Prioritize questions based on:
   - Potential impact on trading decisions
   - Information availability
   - Time sensitivity

Generate 3 specific follow-up questions that would help in making a better trading decision.
Explain your reasoning for each question.

Format the response as a JSON array of objects:
[
    {{
        "question": "the question",
        "category": "area of investigation",
        "reasoning": "explanation of why this question is important",
        "expected_impact": "how the answer could affect trading decisions"
    }},
    ...
]"""
        
        response = self._generate_response(prompt)
        try:
            questions = json.loads(response)
            
            # Print question generation process
            print("\n❓ Question Generation Process:")
            for i, q in enumerate(questions, 1):
                self._print_analysis_step(i, f"Question {i}", {
                    "question": q.get("question", ""),
                    "category": q.get("category", ""),
                    "reasoning": q.get("reasoning", ""),
                    "expected_impact": q.get("expected_impact", "")
                })
            
            return questions
        except:
            return [
                {
                    "question": f"What are the main competitors of {ticker}?",
                    "category": "Industry Analysis",
                    "reasoning": "Understanding competitive position",
                    "expected_impact": "Assess market share stability"
                },
                {
                    "question": f"What are the current market risks for {ticker}?",
                    "category": "Risk Assessment",
                    "reasoning": "Identifying potential threats",
                    "expected_impact": "Risk management strategy"
                },
                {
                    "question": f"What are the growth prospects for {ticker}?",
                    "category": "Growth Analysis",
                    "reasoning": "Evaluating future potential",
                    "expected_impact": "Long-term investment viability"
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