import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment variables
MONGODB_URI = os.getenv("MONGODB_URI")
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
SEARXNG_URL = os.getenv("SEARXNG_URL")

# Trading settings
INITIAL_BALANCE = 1000000  # Paper trading initial balance
MAX_POSITIONS = 10  # Maximum number of concurrent positions
RISK_PERCENTAGE = 2  # Maximum risk per trade as percentage

# Database collections
DB_NAME = "stockbot"
COLLECTIONS = {
    "trades": "trades",
    "news": "news",
    "watchlist": "watchlist",
    "summary": "summary"
}

# Trading personalities
PERSONALITIES = [
    "Conservative",
    "Moderate",
    "Aggressive",
    "Data-Driven",
    "News-Focused",
    "Trend-Following",
    "Counter-Trend",
    "Technical",
    "Fundamental"
] 