import os
from typing import List

class RAGPipeline:
    def __init__(self, data_dir="data/rules"):
        self.data_dir = data_dir
        self.documents = []
        self.ingest_rules()

    def ingest_rules(self):
        """
        Loads all text files from the data directory.
        """
        self.documents = []
        if not os.path.exists(self.data_dir):
            return

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".txt"):
                path = os.path.join(self.data_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Simple chunking by paragraph (split by double newline)
                        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
                        for chunk in chunks:
                            self.documents.append({
                                "source": filename,
                                "text": chunk
                            })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        print(f"Ingested {len(self.documents)} text chunks.")

    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """
        Simple keyword-based retrieval for the prototype.
        In production, this would use vector embeddings (e.g., FAISS/Chroma).
        """
        if not self.documents:
            return []

        # Simple scoring: count query word overlaps
        query_words = set(query.lower().split())
        scored_docs = []

        for doc in self.documents:
            score = 0
            doc_text_lower = doc["text"].lower()
            for word in query_words:
                if word in doc_text_lower:
                    score += 1
            
            if score > 0:
                scored_docs.append((score, doc))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [item[1] for item in scored_docs[:top_k]]
