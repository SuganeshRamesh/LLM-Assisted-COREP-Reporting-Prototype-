from src.retrieval.embeddings import EmbeddingGenerator
from src.retrieval.vector_store import VectorStore
import json
import os
import uuid

class Retriever:
    def __init__(self, kb_path="data/knowledge_base/pra_rulebook_kb.json"):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        self.kb_path = kb_path
        self._initialize_kb()

    def _initialize_kb(self):
        """
        Loads KB from JSON and ingests into Vector Store if empty or needed.
        For prototype, we'll simple check if collection is empty or just upsert all (idempotent).
        """
        if not os.path.exists(self.kb_path):
            print(f"Warning: KB file not found at {self.kb_path}")
            return

        with open(self.kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        documents = []
        texts_to_embed = []

        for item in data:
            # Create a unique ID or use article ID
            doc_id = item.get("article", str(uuid.uuid4()))
            text = f"{item['article']} - {item['section']}\n{item['text']}"
            
            # Metadata must be flat dict for Chroma
            metadata = {
                "article": item.get("article", ""),
                "section": item.get("section", ""),
                "tags": ",".join(item.get("tags", []))
            }
            
            documents.append({
                "id": doc_id,
                "text": text,
                "metadata": metadata
            })
            texts_to_embed.append(text)

        if documents:
            embeddings = self.embedding_generator.generate_batch(texts_to_embed)
            self.vector_store.add_documents(documents, embeddings)
            print(f"Ingested {len(documents)} articles into Vector Store.")

    def retrieve(self, query: str, top_k: int = 5):
        """
        Retrieves relevant documents for a query.
        """
        query_embedding = self.embedding_generator.generate(query)
        results = self.vector_store.query(query_embedding, n_results=top_k)
        
        # Format results
        # Chroma returns lists of lists
        formatted_results = []
        if results and results['documents']:
            num_results = len(results['documents'][0])
            for i in range(num_results):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
