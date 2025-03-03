import os
import numpy as np
import faiss
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from app.core.config_settings import Settings

class VectorDB:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.index_path = Path(settings.VECTOR_DB_PATH)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Separate indices for cocktails and user memories
        self.cocktail_index = None
        self.memory_index = None
        
        # Mappings for data lookup
        self.cocktail_data = {}  # id -> cocktail data
        self.cocktail_ids = []   # index position -> id
        self.memory_data = {}    # session_id -> memory data
        self.memory_ids = []     # index position -> session_id
        
    def initialize(self):
        """Initialize or load existing vector indices"""
        # Initialize cocktail index
        cocktail_index_path = self.index_path / "cocktail_index.faiss"
        cocktail_data_path = self.index_path / "cocktail_data.pkl"
        
        if cocktail_index_path.exists() and cocktail_data_path.exists():
            self.cocktail_index = faiss.read_index(str(cocktail_index_path))
            with open(cocktail_data_path, 'rb') as f:
                self.cocktail_data, self.cocktail_ids = pickle.load(f)
        else:
            # This will be populated later when processing the cocktail data
            self.cocktail_index = None
        
        # Initialize memory index
        memory_index_path = self.index_path / "memory_index.faiss"
        memory_data_path = self.index_path / "memory_data.pkl"
        
        if memory_index_path.exists() and memory_data_path.exists():
            self.memory_index = faiss.read_index(str(memory_index_path))
            with open(memory_data_path, 'rb') as f:
                self.memory_data, self.memory_ids = pickle.load(f)
        else:
            # Create a new memory index
            self.memory_index = faiss.IndexFlatL2(self.embedding_model.get_sentence_embedding_dimension())
            self.memory_data = {}
            self.memory_ids = []
            self._save_memory_index()
    
    def create_cocktail_index(self, cocktails: List[Dict[str, Any]]):
        """Create vector embeddings for cocktails"""
        
        if self.cocktail_index is None:
            print("Cocktail index is not initialized. Initializing now.")
            dimension = self.embedding_model.get_sentence_embedding_dimension()
            self.cocktail_index = faiss.IndexFlatL2(dimension)
        # Clear existing data
        self.cocktail_data = {}
        self.cocktail_ids = []
        
        # Create embeddings for each cocktail
        cocktail_texts = []
        for cocktail in cocktails:
            # Create a text representation combining name and ingredients
            text = f"{cocktail['name']} {' '.join(cocktail['ingredients'])}"
            cocktail_texts.append(text)
            
            # Store cocktail data
            self.cocktail_data[cocktail['id']] = cocktail
            self.cocktail_ids.append(cocktail['id'])
        
        # Convert texts to embeddings
        embeddings = self.embedding_model.encode(cocktail_texts)
        
        # Add to index
        self.cocktail_index.add(np.array(embeddings).astype('float32'))
        
        # Save index and data
        self._save_cocktail_index()
    
    def search_similar_cocktails(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar cocktails based on a text query"""
        if self.cocktail_index is None:
            return []
        
        # Create embedding for the query
        query_embedding = self.embedding_model.encode([query])
        
        # Search the index
        distances, indices = self.cocktail_index.search(
            np.array(query_embedding).astype('float32'), k
        )
        
        # Retrieve results
        results = []
        for idx in indices[0]:
            if idx < len(self.cocktail_ids):
                cocktail_id = self.cocktail_ids[idx]
                results.append(self.cocktail_data[cocktail_id])
        
        return results
    
    def search_similar_cocktails_by_name(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar cocktails based on a cocktail name"""
        # Find the cocktail first
        found_cocktail = None
        for cocktail_id, cocktail in self.cocktail_data.items():
            if cocktail['name'].lower() == name.lower():
                found_cocktail = cocktail
                break
        
        if not found_cocktail:
            # Try a fuzzy search if exact match not found
            return self.search_similar_cocktails(name, k)
        
        # Create a query from the cocktail's ingredients
        query = " ".join(found_cocktail['ingredients'])
        
        # Find similar cocktails
        return self.search_similar_cocktails(query, k+1)[1:k+1]  # Skip the first one as it's likely the same cocktail
    
    def store_user_memory(self, session_id: str, data: Dict[str, Any]):
        """Store user preferences in the vector database"""
        if self.memory_index is None:
            print("Memory index is not initialized. Initializing now.")
            # Initialize memory index if it is not initialized
            self.memory_index = faiss.IndexFlatL2(self.embedding_model.get_sentence_embedding_dimension())
        # Create a text representation of the user's preferences
        ingredients = data.get('favorite_ingredients', [])
        cocktails = data.get('favorite_cocktails', [])
        
        text = f"User {session_id} likes ingredients: {' '.join(ingredients)}. "
        text += f"User {session_id} likes cocktails: {' '.join(cocktails)}."
        
        # Check if user already exists
        existing_idx = -1
        for idx, sid in enumerate(self.memory_ids):
            if sid == session_id:
                existing_idx = idx
                break
        
        # Create embedding
        embedding = self.embedding_model.encode([text])
        
        if existing_idx >= 0:
            # Replace existing entry
            self.memory_data[session_id] = data
            
            # We can't update FAISS index directly, so we need to rebuild it
            all_embeddings = []
            self.memory_ids = []
            
            for sid, mem_data in self.memory_data.items():
                self.memory_ids.append(sid)
                
                mem_ingredients = mem_data.get('favorite_ingredients', [])
                mem_cocktails = mem_data.get('favorite_cocktails', [])
                
                mem_text = f"User {sid} likes ingredients: {' '.join(mem_ingredients)}. "
                mem_text += f"User {sid} likes cocktails: {' '.join(mem_cocktails)}."
                
                mem_embedding = self.embedding_model.encode([mem_text])
                all_embeddings.append(mem_embedding[0])
            
            # Reset index and add all embeddings
            self.memory_index = faiss.IndexFlatL2(self.embedding_model.get_sentence_embedding_dimension())
            
            self.memory_index.add(np.array(all_embeddings).astype('float32'))
        else:
            # Add new entry
            self.memory_data[session_id] = data
            self.memory_ids.append(session_id)
            self.memory_index.add(np.array(embedding).astype('float32'))
        
        # Save memory index and data
        self._save_memory_index()
    
    def get_user_memory(self, session_id: str) -> Dict[str, Any]:
        """Retrieve user preferences by session ID"""
        if session_id in self.memory_data:
            return self.memory_data[session_id]
        return {'favorite_ingredients': [], 'favorite_cocktails': []}
    
    def _save_cocktail_index(self):
        """Save cocktail index and data to disk"""
        cocktail_index_path = self.index_path / "cocktail_index.faiss"
        cocktail_data_path = self.index_path / "cocktail_data.pkl"
        
        faiss.write_index(self.cocktail_index, str(cocktail_index_path))
        with open(cocktail_data_path, 'wb') as f:
            pickle.dump((self.cocktail_data, self.cocktail_ids), f)
    
    def _save_memory_index(self):
        """Save memory index and data to disk"""
        memory_index_path = self.index_path / "memory_index.faiss"
        memory_data_path = self.index_path / "memory_data.pkl"
        
        faiss.write_index(self.memory_index, str(memory_index_path))
        with open(memory_data_path, 'wb') as f:
            pickle.dump((self.memory_data, self.memory_ids), f)