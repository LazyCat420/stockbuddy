# StockBot

StockBot is an intelligent trading bot that uses market news, technical analysis, and AI-powered decision making to simulate paper trading on the stock market. It supports multiple modes of analysis:

- **General Mode:** Analyzes overall market trends and generates a watchlist.
- **Sector Mode:** Analyzes news and stocks from a specific market sector.
- **Single Stock Mode:** Provides in-depth analysis of a specific stock, including follow-up AI queries.
- **Status, History & Performance:** Retrieve account information, trading history, and performance metrics.

## Prerequisites

- **Python Version:** Python 3.8 or later
- **MongoDB:** A running MongoDB instance (local or remote).  
- **Environment Variables:** Create a `.env` file (or set these in your environment) with the following variables:
  - `MONGODB_URI` – MongoDB connection string.
  - `OLLAMA_URL` – Base URL for the Ollama API.
  - `OLLAMA_API_KEY` – API key for Ollama (required, but unused in logic).
  - `OLLAMA_MODEL` – The Ollama model identifier.
  - `SEARXNG_URL` – URL for the SearxNG instance.

## Installation

1. **Clone the Repository**

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create and Activate Virtual Environment**

   On macOS/Linux:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   On Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r stockbot-claude/requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the project root with the following content:
   ```env
   MONGODB_URI=your_mongodb_connection_string
   OLLAMA_URL=https://your-ollama-url.com
   OLLAMA_API_KEY=your_ollama_api_key
   OLLAMA_MODEL=your_ollama_model
   SEARXNG_URL=https://your-searxng-url.com
   ```

## Usage

Navigate to the project root (where `main.py` is located) and use the following commands:

1. **General Market Analysis**

   ```bash
   python stockbot-claude/main.py general
   ```

2. **Sector Analysis**

   Replace `<sector_name>` with the sector you want to analyze (e.g., `technology`, `finance`):

   ```bash
   python stockbot-claude/main.py sector <sector_name>
   ```

3. **Single Stock Analysis**

   Replace `<ticker>` with a valid stock ticker (e.g., `AAPL`):

   ```bash
   python stockbot-claude/main.py stock <ticker>
   ```

4. **Retrieve Account Status**

   ```bash
   python stockbot-claude/main.py status
   ```

5. **Retrieve Trading History**

   ```bash
   python stockbot-claude/main.py history
   ```

6. **Retrieve Performance Summary**

   ```bash
   python stockbot-claude/main.py performance
   ```

## Project Structure

- **stockbot-claude/**
  - `main.py` – Entry point of the application.
  - `config.py` – Configuration and environment variable loading.
  - `database.py` – MongoDB interactions.
  - `ai_analysis.py` – AI interactions via Ollama.
  - `stock_data.py` – Retrieves and processes stock data using yfinance.
  - `news_search.py` – Executes news searches using SearxNG via LangChain.
  - `general_mode.py` – Implements General Market Analysis.
  - `sector_mode.py` – Implements Sector Analysis.
  - `single_stock_mode.py` – Implements Single Stock Mode.
- **requirements.txt** – List of global Python dependencies.


## Models List
athene-v2:latest 
granite3-dense:8b
## Debugging & Logs

The bot prints detailed console logs at every step for debugging purposes. If you encounter an error, check the console output for tracebacks and log messages that indicate where the error occurred.

## Contributing

Feel free to fork the repository and submit pull requests. For any issues, please open an issue with detailed reproduction steps.

## License

This project is licensed under the MIT License.


