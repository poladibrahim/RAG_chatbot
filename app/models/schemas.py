from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatInput(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    detected_preferences: List[str] = []

class Cocktail(BaseModel):
    id: str
    name: str
    ingredients: List[str]
    is_alcoholic: bool
    instructions: str
    
class UserMemory(BaseModel):
    session_id: str
    favorite_ingredients: List[str] = []
    favorite_cocktails: List[str] = []
    
class SimilarCocktailRequest(BaseModel):
    cocktail_name: str
    
class CocktailRecommendationRequest(BaseModel):
    session_id: str
    count: int = 5