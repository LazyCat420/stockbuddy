import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

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
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return self._create_error_response(f"No data found for {ticker}")
            
            # Calculate technical indicators
            hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
            hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
            hist['RSI'] = self._calculate_rsi(hist['Close'])
            
            latest_price = hist['Close'].iloc[-1]
            
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
                "success": True
            }
            
            # Convert all numeric values to standard Python types
            return self._convert_dict_values(data)
            
        except Exception as e:
            print(f"Error fetching data for {ticker}: {str(e)}")
            return self._create_error_response(str(e))
    
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
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
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