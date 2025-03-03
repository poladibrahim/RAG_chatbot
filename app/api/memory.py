from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any

from app.models.schemas import UserMemory, CocktailRecommendationRequest
from app.services.memory import MemoryService
from app.services.cocktail import CocktailService
from app.core.config_settings import Settings
from app.core.vector_db import VectorDB

# from app.main import memory_service, cocktail_service

settings = Settings()
vector_db = VectorDB(settings)

cocktail_service = CocktailService(vector_db)
memory_service = MemoryService(vector_db)




router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/{session_id}", response_model=UserMemory)
async def get_memory(session_id: str) -> UserMemory:
    """
    Get user memory by session ID
    """
    try:
        return memory_service.get_user_memory(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory: {str(e)}")

@router.delete("/{session_id}")
async def clear_memory(session_id: str) -> Dict[str, str]:
    """
    Clear user memory by session ID
    """
    try:
        memory_service.clear_user_memory(session_id)
        return {"status": "success", "message": "Memory cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")

@router.post("/recommend", response_model=List[Dict[str, Any]])
async def recommend_from_favorites(request: CocktailRecommendationRequest) -> List[Dict[str, Any]]:
    """
    Recommend cocktails based on user's favorite ingredients
    """
    try:
        user_memory = memory_service.get_user_memory(request.session_id)
        favorite_ingredients = user_memory.favorite_ingredients
        
        if not favorite_ingredients:
            return []
        
        # Get recommendations
        recommendations = cocktail_service.recommend_cocktails_from_ingredients(
            favorite_ingredients, 
            request.count
        )
        
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recommending cocktails: {str(e)}")