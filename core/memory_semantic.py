# core/memore_semantic.py
import logging
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class SemanticMemoryEngine:
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2"):
        self.chroma_client = chromadb.Client()
        self.semantic_collection = self.chroma_client.get_or_create_collection(name="episodic_memories")
        self.embedding_model = SentenceTransformer(embedding_model_name)

    def encode(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()

    def add_memory(self, content, embedding, metadata, memory_id):
        self.semantic_collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[memory_id]
        )

    def semantic_recall(self, query):
        """Retrieve semantically similar memories from ChromaDB."""
        try:
            embedding = self.embedding_model.encode(query).tolist()
            results = self.semantic_collection.query(
                query_embeddings=[embedding],
                n_results=5,
            )
            return results['documents'][0] if results['documents'] else []
        except Exception as e:
            logging.error(f"[Semantic Recall Error] {e}")
            return []

    def get_sentiment_color(self, content):
        sentiment_map = {
            "warm": ["love", "hope", "happiness", "joy", "bright", "sunshine", "comfort"],
            "melancholy": ["sad", "grief", "loss", "lonely", "tears", "heartache", "rain"],
            "bright": ["bright", "excited", "joyful", "future", "dream", "inspired", "adventure"],
            "neutral": ["calm", "peace", "normal", "quiet", "neutral", "balanced"],
            "anxious": ["nervous", "worried", "fear", "stress", "overwhelmed", "anxiety"],
            "reflective": ["memory", "remember", "reflection", "past", "thinking"],
        }

        content_lower = content.lower()
        sentiment_scores = {key: sum(1 for word in words if word in content_lower) for key, words in sentiment_map.items()}
        sentiment_color = max(sentiment_scores, key=sentiment_scores.get)
        return sentiment_color

    def get_sentiment_strength(self, sentiment_scores: Dict[str, float]) -> Dict[str, float]:
        max_score = max(sentiment_scores.values())
        return {key: value / max_score for key, value in sentiment_scores.items()}
