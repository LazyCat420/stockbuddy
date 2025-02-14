# web_scraper_ollama.py
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings  # Updated import
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
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Initialize Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        print("✅ ChromaDB initialized with persistent storage")
        
        print("✅ WebScraper initialized")
    
    def _get_with_retry(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Get URL content with Selenium WebDriver"""
        print("\n=== SCRAPING ATTEMPT STARTED ===")
        print(f"🌐 URL: {url}")
        
        for attempt in range(max_retries):
            try:
                print(f"\n📝 Attempt {attempt + 1}/{max_retries}")
                
                # Initialize WebDriver
                driver = webdriver.Chrome(options=self.chrome_options)
                driver.get(url)
                
                # Wait for page load with longer timeout
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Try to find article content first
                content_selectors = [
                    "article",
                    ".article-content",
                    ".story-content",
                    ".content-article",
                    "main",
                    ".main-content"
                ]
                
                text_content = ""
                for selector in content_selectors:
                    try:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        text_content = element.text
                        if text_content and len(text_content) > 100:
                            break
                    except:
                        continue
                
                # Fallback to body if no article content found
                if not text_content:
                    text_content = driver.find_element(By.TAG_NAME, "body").text
                
                # Debug content
                print("\n=== CONTENT PREVIEW ===")
                print(f"📊 Content length: {len(text_content)} characters")
                print("\nFirst 500 characters:")
                print("---START---")
                print(text_content[:500])
                print("---END---")
                
                driver.quit()
                
                if len(text_content) < 100:
                    print("⚠️ Warning: Content too short!")
                    continue
                    
                return text_content
                
            except Exception as e:
                print(f"\n❌ Scraping attempt {attempt + 1} failed:")
                print(f"Error type: {type(e).__name__}")
                print(f"Error message: {str(e)}")
                if 'driver' in locals():
                    driver.quit()
                
                if attempt < max_retries - 1:
                    print(f"Retrying in 5 seconds...")
                    time.sleep(5)
                continue
        
        print(f"\n❌ All {max_retries} scraping attempts failed")
        return None

    def scrape_and_analyze(self, url: str) -> Dict:
        """Scrape and analyze webpage content"""
        print("\n=== Starting Scrape and Analysis ===")
        print(f"🎯 Target URL: {url}")
        
        try:
            # Validate URL
            if not url:
                return {"success": False, "error": "Empty URL provided"}
            if not url.startswith(('http://', 'https://')):
                return {"success": False, "error": "Invalid URL format"}
            
            # Get content
            content = self._get_with_retry(url)
            if not content:
                return {
                    "success": False,
                    "error": "Failed to fetch content",
                    "url": url
                }
            
            # Create QA chain with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"\n🔄 Analysis attempt {attempt + 1}/{max_retries}")
                    qa_chain = self._create_qa_chain(content)
                    
                    # Run analysis steps
                    summary = qa_chain.invoke("Summarize the main points of this article in 3-4 sentences.")
                    print(f"✅ Summary generated: {summary['result']}")
                    
                    sentiment = qa_chain.invoke("What is the sentiment of this article regarding the stock or market? Respond with: bullish, bearish, or neutral and explain why.")
                    print(f"✅ Sentiment analyzed: {sentiment['result']}")
                    
                    key_points = qa_chain.invoke("What are the 3 most important facts or insights from this article?")
                    print(f"✅ Key points extracted: {key_points['result']}")
                    
                    return {
                        "success": True,
                        "url": url,
                        "content": content[:1000] + "...",
                        "summary": summary["result"],
                        "sentiment": sentiment["result"],
                        "key_points": key_points["result"]
                    }
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"⚠️ Attempt {attempt + 1} failed, retrying in 5 seconds...")
                    print(f"Error: {str(e)}")
                    time.sleep(5)
                
        except Exception as e:
            print("\n❌ Analysis failed:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

    def _create_qa_chain(self, content: str) -> RetrievalQA:
        """Create a QA chain from content"""
        try:
            print("\n🔄 Creating QA Chain...")
            
            # Split content into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            chunks = text_splitter.split_text(content)
            print(f"📚 Split content into {len(chunks)} chunks")
            
            # Process chunks with ChromaDB
            chroma_result = self.chroma_handler.process_chunks(chunks)
            if not chroma_result["success"]:
                raise ValueError(f"Failed to process chunks: {chroma_result['error']}")
            
            # Create proper BaseRetriever implementation with Pydantic field
            class ChromaRetriever(BaseRetriever):
                chroma_handler: Any = Field(description="ChromaDB handler instance")
                
                def __init__(self, chroma_handler: Any):
                    super().__init__(chroma_handler=chroma_handler)
                
                def get_relevant_documents(self, query: str) -> List[Document]:
                    """Get relevant documents for a query"""
                    try:
                        texts = self.chroma_handler.query_similar(query)
                        # Convert to Document objects
                        return [Document(page_content=text) for text in texts]
                    except Exception as e:
                        print(f"Error in retrieval: {str(e)}")
                        return []
                
                async def aget_relevant_documents(self, query: str) -> List[Document]:
                    """Async version of get_relevant_documents"""
                    return self.get_relevant_documents(query)
            
            # Create LLM and QA chain
            print("🤖 Initializing LLM...")
            from langchain_ollama import OllamaLLM  # Updated import
            
            llm = OllamaLLM(
                model=self.ollama_model,
                base_url=self.base_url
            )
            
            retriever = ChromaRetriever(chroma_handler=self.chroma_handler)
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                verbose=True
            )
            
            print("✅ QA Chain created successfully")
            return qa_chain
            
        except Exception as e:
            print("\n❌ Error creating QA chain:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Full traceback:")
            import traceback
            print(traceback.format_exc())
            raise

if __name__ == '__main__':
    # Replace with the URL you want to scrape
    target_url = "https://www.example.com"  # Replace with the URL you want to scrape
    ollama_model_name = OLLAMA_MODEL # Or another Ollama model you have, e.g., "mistral"

    scraper_chain = WebScraper()

    result = scraper_chain.scrape_and_analyze(target_url)

    print(f"Query: {target_url}")
    print(f"Analysis Result: {result}")