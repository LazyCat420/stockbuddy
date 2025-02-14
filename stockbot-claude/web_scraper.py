# web_scraper_ollama.py
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama
from config import OLLAMA_MODEL, OLLAMA_URL, OLLAMA_EMBEDDING_URL, OLLAMA_EMBEDDING_MODEL
from proxy_handler import ProxyHandler
import requests
from typing import Dict, Optional, List, Any
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromadb
import os
from chromadb_handler import ChromaDBHandler
from langchain.schema import BaseRetriever, Document
from pydantic import Field
from datetime import datetime
import random

# Remove circular import
# from news_search import NewsSearcher

class WebScraper:
    def __init__(self):
        print("\n=== Initializing WebScraper ===")
        self.proxy_handler = ProxyHandler()
        self.base_url = OLLAMA_URL
        self.embedding_url = OLLAMA_EMBEDDING_URL
        self.ollama_model = OLLAMA_MODEL
        self.embedding_model = OLLAMA_EMBEDDING_MODEL
        self.chroma_handler = ChromaDBHandler()
        
        # Initialize Chrome options with better defaults
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        
        # Add better SSL handling
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--ignore-ssl-errors')
        self.chrome_options.add_argument('--allow-insecure-localhost')
        
        # Add anti-bot detection bypass
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add better user agent
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        print("✅ ChromaDB initialized with persistent storage")
        
        # Initialize webdriver with better error handling
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            # Execute CDP commands to prevent detection
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            print("✅ WebScraper initialized")
        except Exception as e:
            print(f"❌ Failed to initialize WebScraper: {str(e)}")
            raise
    
    def _determine_source(self, url: str) -> str:
        """Determine the source type from URL"""
        url_lower = url.lower()
        if 'yahoo.com' in url_lower:
            return 'Yahoo Finance'
        elif 'marketwatch.com' in url_lower:
            return 'MarketWatch'
        elif 'reuters.com' in url_lower:
            return 'Reuters'
        elif 'bloomberg.com' in url_lower:
            return 'Bloomberg'
        elif 'cnbc.com' in url_lower:
            return 'CNBC'
        elif 'fool.com' in url_lower:
            return 'Motley Fool'
        elif 'seekingalpha.com' in url_lower:
            return 'Seeking Alpha'
        else:
            return 'Financial News'

    def scrape_and_analyze(self, url: str) -> Dict:
        """Scrape webpage content and return structured data"""
        print("\n=== Starting Web Scraping ===")
        print(f"🎯 Target URL: {url}")
        
        try:
            # Validate URL
            if not url:
                return {"success": False, "error": "Empty URL provided"}
            if not url.startswith(('http://', 'https://')):
                return {"success": False, "error": "Invalid URL format"}

            print("\n=== SCRAPING ATTEMPT STARTED ===")
            print(f"🌐 URL: {url}")
            
            max_retries = 3
            content = ""
            
            for attempt in range(max_retries):
                try:
                    print(f"\n📝 Attempt {attempt + 1}/{max_retries}")
                    
                    # Clear cookies and cache before each attempt
                    self.driver.delete_all_cookies()
                    
                    # Add random delay to avoid detection
                    time.sleep(2 + random.random() * 3)
                    
                    # Load the page with wait
                    self.driver.get(url)
                    
                    # Wait for body with longer timeout
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Wait for dynamic content with better error handling
                    try:
                        WebDriverWait(self.driver, 10).until(
                            lambda driver: driver.execute_script("return document.readyState") == "complete"
                        )
                    except:
                        print("⚠️ Page load state check timed out, continuing anyway")
                    
                    # Scroll to load dynamic content
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    
                    # Extract text content from different elements
                    selectors = {
                        'title': 'head title',
                        'description': 'meta[name="description"]',
                        'article': 'article',
                        'main': 'main',
                        'paragraphs': 'p',
                        'headers': ['h1', 'h2', 'h3'],
                        # Add Yahoo Finance specific selectors
                        'yahoo_price': '[data-test="qsp-price"]',
                        'yahoo_summary': '#quote-summary',
                        'yahoo_stats': '#quote-summary [data-test="qsp-statistics"]'
                    }
                    
                    content_parts = []
                    
                    # Get title
                    try:
                        title = self.driver.find_element(By.CSS_SELECTOR, selectors['title']).text
                        content_parts.append(f"Title: {title}")
                    except Exception as e:
                        print(f"⚠️ Failed to get title: {str(e)}")
                    
                    # Get meta description
                    try:
                        description = self.driver.find_element(By.CSS_SELECTOR, selectors['description']).get_attribute('content')
                        content_parts.append(f"Description: {description}")
                    except Exception as e:
                        print(f"⚠️ Failed to get description: {str(e)}")
                    
                    # Try Yahoo Finance specific elements first
                    if 'yahoo.com' in url:
                        try:
                            price = self.driver.find_element(By.CSS_SELECTOR, selectors['yahoo_price']).text
                            content_parts.append(f"Current Price: {price}")
                        except:
                            pass
                            
                        try:
                            summary = self.driver.find_element(By.CSS_SELECTOR, selectors['yahoo_summary']).text
                            content_parts.append(f"Summary: {summary}")
                        except:
                            pass
                            
                        try:
                            stats = self.driver.find_element(By.CSS_SELECTOR, selectors['yahoo_stats']).text
                            content_parts.append(f"Statistics: {stats}")
                        except:
                            pass
                    
                    # Get article content
                    try:
                        article = self.driver.find_element(By.TAG_NAME, 'article').text
                        content_parts.append(f"Article Content: {article}")
                    except:
                        # If no article tag, try main content
                        try:
                            main = self.driver.find_element(By.TAG_NAME, 'main').text
                            content_parts.append(f"Main Content: {main}")
                        except:
                            # If no main tag, get paragraphs
                            paragraphs = self.driver.find_elements(By.TAG_NAME, 'p')
                            for p in paragraphs:
                                try:
                                    content_parts.append(p.text)
                                except:
                                    continue
                    
                    # Get headers
                    for header in selectors['headers']:
                        try:
                            headers = self.driver.find_elements(By.TAG_NAME, header)
                            for h in headers:
                                try:
                                    content_parts.append(h.text)
                                except:
                                    continue
                        except:
                            continue
                    
                    content = '\n'.join(filter(None, content_parts))
                    
                    if content:
                        print("\n=== CONTENT PREVIEW ===")
                        print(f"📊 Content length: {len(content)} characters")
                        print("\nFirst 500 characters:")
                        print("---START---")
                        print(content[:500])
                        print("---END---")
                        break
                    else:
                        print("⚠️ No content extracted, retrying...")
                        
                except Exception as e:
                    print(f"\n⚠️ Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(5)
            
            # Structure the scraped data
            scraped_data = {
                "success": True,
                "url": url,
                "content": content,
                "metadata": {
                    "source": self._determine_source(url),
                    "timestamp": str(datetime.now()),
                    "content_length": len(content)
                }
            }
            
            print(f"\n✅ Successfully scraped {scraped_data['metadata']['source']}")
            return scraped_data
            
        except Exception as e:
            print("\n❌ Scraping failed:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
        finally:
            try:
                # Clear cookies and cache after scraping
                self.driver.delete_all_cookies()
            except:
                pass

    def __del__(self):
        """Clean up Selenium driver"""
        try:
            self.driver.quit()
        except:
            pass

if __name__ == '__main__':
    # Replace with the URL you want to scrape
    target_url = "https://www.example.com"  # Replace with the URL you want to scrape
    ollama_model_name = OLLAMA_MODEL # Or another Ollama model you have, e.g., "mistral"

    scraper_chain = WebScraper()

    result = scraper_chain.scrape_and_analyze(target_url)

    print(f"Query: {target_url}")
    print(f"Analysis Result: {result}")
    print(f"Analysis Result: {result}")