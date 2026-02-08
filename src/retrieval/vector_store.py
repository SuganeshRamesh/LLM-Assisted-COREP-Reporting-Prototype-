import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any

class VectorStore:
    def __init__(self, collection_name="pra_rulebook"):
        # persistent storage
        db_path = os.path.join(os.getcwd(), "data", "chroma_db")
        if not os.path.exists(db_path):
            os.makedirs(db_path)
            
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Adds documents to the store.
        documents: list of dicts with 'id', 'text', 'metadata'
        embeddings: list of embedding vectors
        """
        if not documents:
            return

        ids = [doc['id'] for doc in documents]
        texts = [doc['text'] for doc in documents]
        metadatas = [doc['metadata'] for doc in documents]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def query(self, query_embedding: List[float], n_results: int = 5):
        """
        Queries the store.
        """
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
