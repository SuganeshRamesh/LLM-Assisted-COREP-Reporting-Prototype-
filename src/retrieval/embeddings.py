from sentence_transformers import SentenceTransformer
import os

class EmbeddingGenerator:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        # Use a local cache for models to avoid re-downloading
        cache_folder = os.path.join(os.getcwd(), "models_cache")
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)
            
        try:
            self.model = SentenceTransformer(model_name, cache_folder=cache_folder)
        except Exception as e:
            print(f"Error loading embedding model {model_name}: {e}")
            # Fallback or re-raise depending on strictness. For prototype, we re-raise.
            raise e

    def generate(self, text: str):
        """Generates embedding for a single string."""
        if not text:
            return []
        return self.model.encode(text).tolist()

    def generate_batch(self, texts: list):
        """Generates embeddings for a list of strings."""
        if not texts:
            return []
        return self.model.encode(texts).tolist()
