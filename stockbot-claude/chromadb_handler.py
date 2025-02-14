from typing import List, Dict
import chromadb
import time
import requests
from config import OLLAMA_EMBEDDING_URL, OLLAMA_EMBEDDING_MODEL

class ChromaDBHandler:
    def __init__(self):
        print("\n=== Initializing ChromaDB Handler ===")
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.embedding_url = OLLAMA_EMBEDDING_URL
        self.embedding_model = OLLAMA_EMBEDDING_MODEL
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        print("✅ ChromaDB initialized with persistent storage")

    def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings from Ollama"""
        try:
            print(f"\n🔄 Getting embedding for text: {text[:50]}...")
            
            response = requests.post(
                self.embedding_url,
                headers=self.headers,
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            
            # Debug response
            print(f"Response status: {response.status_code}")
            print(f"Response keys: {response.json().keys()}")
            
            # Handle both 'embedding' and 'embeddings' keys
            data = response.json()
            if 'embedding' in data:
                return data['embedding']
            elif 'embeddings' in data:
                return data['embeddings']
            else:
                raise ValueError(f"No embedding found in response: {data}")
            
        except Exception as e:
            print(f"❌ Error getting embedding: {str(e)}")
            raise

    def process_chunks(self, chunks: List[str]) -> Dict:
        """Process text chunks and store in ChromaDB"""
        try:
            print(f"\n🔄 Processing {len(chunks)} chunks...")
            collection_name = "article_embeddings"
            
            # Get or create collection
            try:
                collection = self.chroma_client.get_collection(name=collection_name)
                print("✅ Got existing collection")
            except:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                print("✅ Created new collection")

            # Generate embeddings
            embeddings_list = []
            for i, chunk in enumerate(chunks):
                try:
                    embedding = self.get_embeddings(chunk)
                    embeddings_list.append(embedding)
                    print(f"✅ Chunk {i+1}/{len(chunks)} embedded")
                except Exception as e:
                    print(f"❌ Error processing chunk {i+1}: {str(e)}")
                    continue

            # Add to ChromaDB
            if embeddings_list:
                collection.add(
                    embeddings=embeddings_list,
                    documents=chunks,
                    ids=[f"doc_{int(time.time())}_{i}" for i in range(len(embeddings_list))]
                )
                print(f"✅ Added {len(embeddings_list)} embeddings to ChromaDB")
            
            return {
                "success": True,
                "collection": collection,
                "num_embeddings": len(embeddings_list)
            }

        except Exception as e:
            print(f"❌ Error in process_chunks: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def query_similar(self, query: str, collection_name: str = "article_embeddings", n_results: int = 3) -> List[str]:
        """Query similar documents"""
        try:
            print(f"\n🔍 Querying similar documents for: {query[:50]}...")
            collection = self.chroma_client.get_collection(name=collection_name)
            
            query_embedding = self.get_embeddings(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            print(f"✅ Found {len(results['documents'][0])} similar documents")
            return results["documents"][0]
            
        except Exception as e:
            print(f"❌ Error querying similar documents: {str(e)}")
            return [] 