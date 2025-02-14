from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
import time
import requests
from config import OLLAMA_EMBEDDING_URL, OLLAMA_EMBEDDING_MODEL
import json
from datetime import datetime, timedelta

class ChromaDBHandler:
    def __init__(self):
        print("\n=== Initializing ChromaDB Handler ===")
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")
            print("✅ ChromaDB client initialized")
            
            # Ensure collections exist
            self._ensure_collection("news_analyses")
            self._ensure_collection("trading_decisions")
            self._ensure_collection("sector_analyses")
            print("✅ Collections initialized")
            
        except Exception as e:
            print(f"❌ Failed to initialize ChromaDB: {str(e)}")
            raise
    
    def _ensure_collection(self, collection_name: str) -> None:
        """Ensure a collection exists, create if it doesn't"""
        try:
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"Collection for {collection_name}"}
            )
        except Exception as e:
            print(f"❌ Failed to create collection {collection_name}: {str(e)}")
            raise
    
    def save_analysis(self, collection_name: str, data: Dict) -> bool:
        """Save analysis data to ChromaDB"""
        try:
            print(f"\n💾 Saving to {collection_name}...")
            
            # Get or create collection
            collection = self.client.get_or_create_collection(collection_name)
            
            # Convert analysis to string for embedding
            analysis_str = json.dumps(data["analysis"])
            
            # Generate a unique ID
            doc_id = f"{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Add the document
            collection.add(
                documents=[analysis_str],
                metadatas=[data["metadata"]],
                ids=[doc_id]
            )
            
            print(f"✅ Saved analysis with ID: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save analysis: {str(e)}")
            return False
    
    def get_recent_analyses(self, collection_name: str, limit: int = 10) -> List[Dict]:
        """Get most recent analyses from a collection"""
        try:
            collection = self.client.get_collection(collection_name)
            
            # Query the collection
            results = collection.query(
                query_texts=[""],  # Empty query to get all documents
                n_results=limit
            )
            
            # Parse results
            analyses = []
            for i, doc in enumerate(results["documents"][0]):
                try:
                    analysis = json.loads(doc)
                    metadata = results["metadatas"][0][i]
                    analyses.append({
                        "analysis": analysis,
                        "metadata": metadata
                    })
                except:
                    continue
            
            return analyses
            
        except Exception as e:
            print(f"❌ Failed to get analyses: {str(e)}")
            return []
    
    def search_analyses(self, collection_name: str, query: str, limit: int = 5) -> List[Dict]:
        """Search analyses using semantic similarity"""
        try:
            collection = self.client.get_collection(collection_name)
            
            # Query the collection
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            # Parse results
            analyses = []
            for i, doc in enumerate(results["documents"][0]):
                try:
                    analysis = json.loads(doc)
                    metadata = results["metadatas"][0][i]
                    distance = results["distances"][0][i]
                    analyses.append({
                        "analysis": analysis,
                        "metadata": metadata,
                        "relevance_score": 1 - distance  # Convert distance to similarity score
                    })
                except:
                    continue
            
            return analyses
            
        except Exception as e:
            print(f"❌ Failed to search analyses: {str(e)}")
            return []
    
    def delete_old_analyses(self, collection_name: str, days_old: int = 30) -> bool:
        """Delete analyses older than specified days"""
        try:
            collection = self.client.get_collection(collection_name)
            
            # Calculate cutoff date
            cutoff = datetime.now() - timedelta(days=days_old)
            cutoff_str = cutoff.strftime("%Y-%m-%d")
            
            # Get all documents
            results = collection.query(
                query_texts=[""],
                n_results=1000000  # Large number to get all documents
            )
            
            # Find IDs to delete
            ids_to_delete = []
            for i, metadata in enumerate(results["metadatas"][0]):
                try:
                    doc_date = datetime.strptime(metadata["timestamp"][:10], "%Y-%m-%d")
                    if doc_date < cutoff:
                        ids_to_delete.append(results["ids"][0][i])
                except:
                    continue
            
            if ids_to_delete:
                collection.delete(ids=ids_to_delete)
                print(f"✅ Deleted {len(ids_to_delete)} old analyses")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete old analyses: {str(e)}")
            return False

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
                collection = self.client.get_collection(name=collection_name)
                print("✅ Got existing collection")
            except:
                collection = self.client.create_collection(
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
            collection = self.client.get_collection(name=collection_name)
            
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