import os
import sys
from typing import Dict, Any
from datetime import datetime

from general_mode import GeneralMode
from sector_mode import SectorMode
from single_stock_mode import SingleStockMode
from database import DatabaseHandler
from ai_analysis import AIAnalyzer

class StockBot:
    def __init__(self):
        self.db = DatabaseHandler()
        self.ai = AIAnalyzer()
        self.general_mode = GeneralMode()
        self.sector_mode = SectorMode()
        self.single_stock_mode = SingleStockMode()
        
        # Initialize paper trading account
        self._initialize_account()
    
    def _initialize_account(self):
        """Initialize paper trading account with $1,000,000"""
        try:
            # Check if account already exists
            collection = self.db.db["account"]
            account = collection.find_one({"type": "paper_trading"})
            
            if not account:
                collection.insert_one({
                    "type": "paper_trading",
                    "balance": 1000000,
                    "initial_balance": 1000000,
                    "created_at": datetime.now(),
                    "last_updated": datetime.now()
                })
        except Exception as e:
            print(f"Error initializing account: {str(e)}")
    
    def run_general_mode(self) -> Dict:
        """Run general market analysis mode"""
        print("Running general market analysis mode...")
        return self.general_mode.run()
    
    def run_sector_mode(self, sector: str) -> Dict:
        """Run sector-specific analysis mode"""
        print(f"Running sector analysis mode for {sector}...")
        return self.sector_mode.run(sector)
    
    def run_single_stock_mode(self, ticker: str) -> Dict:
        """Run single stock analysis mode"""
        print(f"Running single stock analysis mode for {ticker}...")
        return self.single_stock_mode.run(ticker)
    
    def get_account_status(self) -> Dict:
        """Get current account status"""
        try:
            collection = self.db.db["account"]
            account = collection.find_one({"type": "paper_trading"})
            
            if account:
                return {
                    "success": True,
                    "balance": account["balance"],
                    "initial_balance": account["initial_balance"],
                    "profit_loss": account["balance"] - account["initial_balance"],
                    "profit_loss_percentage": ((account["balance"] - account["initial_balance"]) / account["initial_balance"]) * 100,
                    "last_updated": account["last_updated"]
                }
            else:
                return {
                    "success": False,
                    "error": "Account not found"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_trading_history(self, limit: int = 50) -> Dict:
        """Get recent trading history"""
        try:
            collection = self.db.db["trades"]
            trades = list(collection.find().sort("timestamp", -1).limit(limit))
            
            return {
                "success": True,
                "trades": trades
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_performance_summary(self) -> Dict:
        """Get overall trading performance summary"""
        try:
            trades_collection = self.db.db["trades"]
            account_collection = self.db.db["account"]
            
            # Get account info
            account = account_collection.find_one({"type": "paper_trading"})
            
            # Get all closed trades
            closed_trades = list(trades_collection.find({"status": "closed"}))
            
            # Calculate statistics
            total_trades = len(closed_trades)
            winning_trades = len([t for t in closed_trades if t["exit_price"] > t["price"]])
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                "success": True,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "current_balance": account["balance"],
                "total_profit_loss": account["balance"] - account["initial_balance"],
                "profit_loss_percentage": ((account["balance"] - account["initial_balance"]) / account["initial_balance"]) * 100
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

def main():
    """Main entry point"""
    bot = StockBot()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <mode> [args]")
        print("Modes:")
        print("  general - Analyze general market conditions")
        print("  sector <sector_name> - Analyze specific sector")
        print("  stock <ticker> - Analyze single stock")
        print("  status - Get account status")
        print("  history - Get trading history")
        print("  performance - Get performance summary")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    try:
        if mode == "general":
            result = bot.run_general_mode()
        elif mode == "sector" and len(sys.argv) > 2:
            result = bot.run_sector_mode(sys.argv[2])
        elif mode == "stock" and len(sys.argv) > 2:
            result = bot.run_single_stock_mode(sys.argv[2])
        elif mode == "status":
            result = bot.get_account_status()
        elif mode == "history":
            result = bot.get_trading_history()
        elif mode == "performance":
            result = bot.get_performance_summary()
        else:
            print("Invalid mode or missing arguments")
            sys.exit(1)
        
        # Print results
        if result["success"]:
            print("\nOperation completed successfully!")
            print("\nResults:")
            for key, value in result.items():
                if key != "success":
                    print(f"{key}: {value}")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
