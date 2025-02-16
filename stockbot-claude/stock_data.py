import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time

class StockDataHandler:
    def __init__(self):
        # Define sector mappings
        self.sector_mapping = {
            "technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
            "tech": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],  # Alias for technology
            "healthcare": ["JNJ", "PFE", "UNH", "ABBV", "MRK"],
            "finance": ["JPM", "BAC", "WFC", "GS", "MS"],
            "energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
            "consumer": ["AMZN", "WMT", "PG", "KO", "PEP"]
        }
    
    def _convert_to_python_type(self, value):
        """Convert numpy/pandas types to standard Python types for JSON serialization"""
        if isinstance(value, (np.integer, np.floating)):
            return float(value)
        elif isinstance(value, np.ndarray):
            return [float(x) for x in value]
        elif isinstance(value, pd.Series):
            return [float(x) for x in value.values]
        elif isinstance(value, pd.Timestamp):
            return str(value)
        return value
    
    def _convert_dict_values(self, d: Dict) -> Dict:
        """Recursively convert dictionary values to Python types"""
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = self._convert_dict_values(v)
            elif isinstance(v, (list, np.ndarray, pd.Series)):
                result[k] = [self._convert_to_python_type(x) for x in v]
            else:
                result[k] = self._convert_to_python_type(v)
        return result
    
    def get_available_sectors(self) -> List[str]:
        """Get list of available sectors"""
        # Remove aliases from the list
        unique_sectors = set(self.sector_mapping.keys()) - {"tech"}  # Remove tech alias
        return sorted(list(unique_sectors))
    
    def get_sector_stocks(self, sector: str) -> List[str]:
        """Get list of stocks in a sector"""
        try:
            print(f"Looking up stocks for sector: {sector}")
            sector = sector.lower()  # Normalize sector name
            stocks = self.sector_mapping.get(sector, [])
            print(f"Found {len(stocks)} stocks in sector mapping")
            if not stocks:
                print(f"No stocks found for sector: {sector}")
                print(f"Available sectors: {', '.join(self.get_available_sectors())}")
            return stocks
        except Exception as e:
            print(f"Error getting sector stocks: {str(e)}")
            return []
    
    def get_stock_data(self, ticker: str, period: str = "1mo") -> Dict:
        """Get stock data for analysis"""
        try:
            print(f"Fetching data for {ticker}...")
            
            # Clean and format the ticker
            ticker = ticker.strip().upper()
            print(f"Formatted ticker: {ticker}")
            
            # Input validation
            if not ticker or not isinstance(ticker, str) or len(ticker) > 5:
                return self._create_error_response(f"Invalid ticker format: {ticker}")
            
            # Create ticker object with retry mechanism
            max_retries = 3
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    stock = yf.Ticker(ticker)
                    
                    # Try to get basic info first to validate ticker
                    info = stock.info
                    if not info:
                        raise ValueError("Empty info response")
                    if 'regularMarketPrice' not in info:
                        raise ValueError("No market price available")
                    
                    print(f"✓ Validated ticker {ticker}")
                    print(f"Company Name: {info.get('longName', 'N/A')}")
                    print(f"Sector: {info.get('sector', 'N/A')}")
                    
                    # Get historical data with error handling
                    hist = stock.history(period=period)
                    if hist.empty:
                        raise ValueError("No historical data available")
                    
                    print(f"✓ Retrieved {len(hist)} historical data points")
                    
                    # Calculate technical indicators with error handling
                    try:
                        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                        hist['RSI'] = self._calculate_rsi(hist['Close'])
                    except Exception as e:
                        print(f"Warning: Error calculating technical indicators: {str(e)}")
                        hist['SMA_20'] = hist['SMA_50'] = hist['RSI'] = float('nan')
                    
                    latest_price = hist['Close'].iloc[-1]
                    print(f"Current Price: ${latest_price:.2f}")
                    
                    data = {
                        "ticker": ticker,
                        "current_price": latest_price,
                        "daily_change": self._calculate_daily_change(hist),
                        "volume": hist['Volume'].iloc[-1],
                        "technical_indicators": {
                            "sma_20": hist['SMA_20'].iloc[-1],
                            "sma_50": hist['SMA_50'].iloc[-1],
                            "rsi": hist['RSI'].iloc[-1]
                        },
                        "price_history": hist['Close'].tolist(),
                        "volume_history": hist['Volume'].tolist(),
                        "success": True,
                        "company_info": {
                            "name": info.get('longName', ''),
                            "sector": info.get('sector', ''),
                            "industry": info.get('industry', '')
                        }
                    }
                    
                    # Convert all numeric values to standard Python types
                    return self._convert_dict_values(data)
                    
                except Exception as e:
                    last_error = str(e)
                    print(f"❌ Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"Retrying in 1 second...")
                        time.sleep(1)
                        continue
                    break
            
            error_msg = f"Failed to fetch data after {max_retries} attempts. Last error: {last_error}"
            print(f"❌ {error_msg}")
            return self._create_error_response(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error fetching data for {ticker}: {str(e)}"
            print(f"❌ {error_msg}")
            return self._create_error_response(error_msg)
    
    def get_market_overview(self) -> Dict:
        """Get overview of major market indices"""
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT']  # S&P 500, Dow Jones, NASDAQ, Russell 2000
        
        overview = {}
        for index in indices:
            try:
                data = self.get_stock_data(index, period="1d")
                if data["success"]:
                    overview[index] = {
                        "price": data["current_price"],
                        "daily_change": data["daily_change"]
                    }
            except Exception as e:
                print(f"Error getting data for {index}: {str(e)}")
        
        return self._convert_dict_values(overview)
    
    def _calculate_rsi(self, prices: pd.Series, periods: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            # Handle empty or invalid price data
            if prices.empty or prices.isna().all():
                return pd.Series([float('nan')] * len(prices))

            # Calculate price changes
            delta = prices.diff()
            
            # Separate gains and losses
            gains = delta.where(delta > 0, 0.0)
            losses = -delta.where(delta < 0, 0.0)
            
            # Calculate rolling averages
            avg_gains = gains.rolling(window=periods, min_periods=1).mean()
            avg_losses = losses.rolling(window=periods, min_periods=1).mean()
            
            # Calculate RS with handling division by zero
            rs = pd.Series([float('nan')] * len(prices))  # Initialize with NaN
            valid_denominator = avg_losses != 0
            rs[valid_denominator] = avg_gains[valid_denominator] / avg_losses[valid_denominator]
            
            # Calculate RSI with proper bounds
            rsi = 100 - (100 / (1 + rs))
            
            # Ensure RSI stays within 0-100 bounds
            rsi = rsi.clip(lower=0, upper=100)
            
            # Replace any remaining invalid values with NaN
            rsi = rsi.replace([np.inf, -np.inf], float('nan'))
            
            return rsi
            
        except Exception as e:
            print(f"Warning: Error calculating RSI: {str(e)}")
            return pd.Series([float('nan')] * len(prices))
    
    def _calculate_daily_change(self, hist: pd.DataFrame) -> float:
        """Calculate daily price change percentage"""
        if len(hist) < 2:
            return 0.0
        
        yesterday_close = hist['Close'].iloc[-2]
        today_close = hist['Close'].iloc[-1]
        
        return float(((today_close - yesterday_close) / yesterday_close) * 100)
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response dictionary"""
        return {
            "success": False,
            "error": error_message,
            "current_price": 0.0,
            "daily_change": 0.0,
            "volume": 0.0,
            "technical_indicators": {
                "sma_20": 0.0,
                "sma_50": 0.0,
                "rsi": 0.0
            },
            "price_history": [],
            "volume_history": []
        }
    
    def get_detailed_financials(self, ticker: str) -> Dict:
        """Get detailed financial data for a stock"""
        try:
            print(f"Fetching detailed financials for {ticker}...")
            stock = yf.Ticker(ticker)
            
            # Get financial data
            info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cash_flow = stock.cashflow
            
            # Process and clean the data
            data = {
                "success": True,
                "ticker": ticker,
                "company_info": {
                    "name": info.get("longName", ""),
                    "sector": info.get("sector", ""),
                    "industry": info.get("industry", ""),
                    "market_cap": info.get("marketCap", 0),
                    "pe_ratio": info.get("trailingPE", 0),
                    "dividend_yield": info.get("dividendYield", 0) if info.get("dividendYield") else 0
                },
                "key_metrics": {
                    "revenue": financials.loc["Total Revenue"].iloc[0] if not financials.empty else 0,
                    "net_income": financials.loc["Net Income"].iloc[0] if not financials.empty else 0,
                    "operating_cash_flow": cash_flow.loc["Operating Cash Flow"].iloc[0] if not cash_flow.empty else 0,
                    "total_assets": balance_sheet.loc["Total Assets"].iloc[0] if not balance_sheet.empty else 0,
                    "total_debt": balance_sheet.loc["Total Debt"].iloc[0] if not balance_sheet.empty else 0
                }
            }
            
            return self._convert_dict_values(data)
            
        except Exception as e:
            print(f"Error fetching detailed financials for {ticker}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ticker": ticker
            }
    
    def get_market_analysis(self, ticker: str) -> Dict:
        """Get comprehensive market analysis for a stock"""
        try:
            print(f"Generating market analysis for {ticker}...")
            stock = yf.Ticker(ticker)
            
            # Get various data points
            hist = stock.history(period="6mo")
            info = stock.info
            
            # Calculate additional technical indicators
            hist['EMA_20'] = hist['Close'].ewm(span=20, adjust=False).mean()
            hist['MACD'] = hist['Close'].ewm(span=12, adjust=False).mean() - hist['Close'].ewm(span=26, adjust=False).mean()
            hist['RSI'] = self._calculate_rsi(hist['Close'])
            hist['Volatility'] = hist['Close'].pct_change().rolling(window=20).std() * (252 ** 0.5)  # Annualized volatility
            
            # Get recent performance
            current_price = hist['Close'].iloc[-1]
            month_ago_price = hist['Close'].iloc[-21] if len(hist) >= 21 else hist['Close'].iloc[0]
            three_month_ago_price = hist['Close'].iloc[-63] if len(hist) >= 63 else hist['Close'].iloc[0]
            
            data = {
                "success": True,
                "ticker": ticker,
                "current_analysis": {
                    "price": current_price,
                    "volume": hist['Volume'].iloc[-1],
                    "rsi": hist['RSI'].iloc[-1],
                    "macd": hist['MACD'].iloc[-1],
                    "volatility": hist['Volatility'].iloc[-1],
                    "ema_20": hist['EMA_20'].iloc[-1]
                },
                "performance": {
                    "1m_return": ((current_price - month_ago_price) / month_ago_price) * 100,
                    "3m_return": ((current_price - three_month_ago_price) / three_month_ago_price) * 100,
                    "avg_volume": hist['Volume'].mean()
                },
                "market_context": {
                    "beta": info.get("beta", 0),
                    "market_cap": info.get("marketCap", 0),
                    "sector": info.get("sector", "Unknown"),
                    "industry": info.get("industry", "Unknown")
                }
            }
            
            return self._convert_dict_values(data)
            
        except Exception as e:
            print(f"Error generating market analysis for {ticker}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ticker": ticker
            } 