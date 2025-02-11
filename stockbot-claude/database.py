from pymongo import MongoClient
from datetime import datetime
from config import MONGODB_URI, DB_NAME, COLLECTIONS

class DatabaseHandler:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DB_NAME]
    
    def save_trade(self, ticker, action, price, quantity, personality, confidence, stop_loss, take_profit):
        """Save trade decision to database"""
        collection = self.db[COLLECTIONS["trades"]]
        trade = {
            "ticker": ticker,
            "action": action,
            "price": price,
            "quantity": quantity,
            "personality": personality,
            "confidence": confidence,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "timestamp": datetime.now(),
            "status": "open"
        }
        return collection.insert_one(trade)
    
    def save_news(self, ticker, news_data, source):
        """Save news data to database"""
        collection = self.db[COLLECTIONS["news"]]
        news_entry = {
            "ticker": ticker,
            "news_data": news_data,
            "source": source,
            "timestamp": datetime.now()
        }
        return collection.insert_one(news_entry)
    
    def update_watchlist(self, tickers, sector=None):
        """Update watchlist with new tickers"""
        collection = self.db[COLLECTIONS["watchlist"]]
        watchlist_entry = {
            "tickers": tickers,
            "sector": sector,
            "timestamp": datetime.now()
        }
        return collection.insert_one(watchlist_entry)
    
    def save_summary(self, mode, actions_taken, performance_metrics):
        """Save trading session summary"""
        collection = self.db[COLLECTIONS["summary"]]
        summary = {
            "mode": mode,
            "actions_taken": actions_taken,
            "performance_metrics": performance_metrics,
            "timestamp": datetime.now()
        }
        return collection.insert_one(summary)
    
    def get_open_positions(self):
        """Get all open trading positions"""
        collection = self.db[COLLECTIONS["trades"]]
        return list(collection.find({"status": "open"}))
    
    def get_recent_news(self, ticker=None, limit=50):
        """Get recent news entries"""
        collection = self.db[COLLECTIONS["news"]]
        query = {} if ticker is None else {"ticker": ticker}
        return list(collection.find(query).sort("timestamp", -1).limit(limit))
    
    def close_position(self, trade_id, exit_price):
        """Close a trading position"""
        collection = self.db[COLLECTIONS["trades"]]
        return collection.update_one(
            {"_id": trade_id},
            {
                "$set": {
                    "status": "closed",
                    "exit_price": exit_price,
                    "closed_at": datetime.now()
                }
            }
        ) 