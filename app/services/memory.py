from typing import List, Dict, Any
from app.core.vector_db import VectorDB
from app.models.schemas import UserMemory

class MemoryService:
    """Service to manage user memory and preferences"""
    
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
    
    def get_user_memory(self, session_id: str) -> UserMemory:
        """Get memory for a specific user"""
        memory_data = self.vector_db.get_user_memory(session_id)
        return UserMemory(
            session_id=session_id,
            favorite_ingredients=memory_data.get('favorite_ingredients', []),
            favorite_cocktails=memory_data.get('favorite_cocktails', [])
        )
    
    def update_user_memory(self, session_id: str, new_preferences: Dict[str, List[str]]) -> UserMemory:
        """Update user memory with new preferences"""
        # Get existing memory
        existing_memory = self.vector_db.get_user_memory(session_id)
        
        # Update with new preferences
        if 'favorite_ingredients' in new_preferences:
            # Add new ingredients, avoiding duplicates
            for ingredient in new_preferences['favorite_ingredients']:
                if ingredient not in existing_memory.get('favorite_ingredients', []):
                    existing_memory.setdefault('favorite_ingredients', []).append(ingredient)
        
        if 'favorite_cocktails' in new_preferences:
            # Add new cocktails, avoiding duplicates
            for cocktail in new_preferences['favorite_cocktails']:
                if cocktail not in existing_memory.get('favorite_cocktails', []):
                    existing_memory.setdefault('favorite_cocktails', []).append(cocktail)
        
        # Store updated memory
        self.vector_db.store_user_memory(session_id, existing_memory)
        
        # Return updated memory
        return UserMemory(
            session_id=session_id,
            favorite_ingredients=existing_memory.get('favorite_ingredients', []),
            favorite_cocktails=existing_memory.get('favorite_cocktails', [])
        )
    
    def clear_user_memory(self, session_id: str) -> None:
        """Clear all memory for a specific user"""
        empty_memory = {'favorite_ingredients': [], 'favorite_cocktails': []}
        self.vector_db.store_user_memory(session_id, empty_memory)