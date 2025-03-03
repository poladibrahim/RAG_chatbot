from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from app.models.schemas import ChatInput, ChatResponse
# from app.services.rag import RAGService
# from app.main import rag_service
from app.core.config_settings import Settings
# from app.api import chat, memory
from app.services.cocktail import CocktailService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.core.vector_db import VectorDB
from app.core.llm import LLM

settings = Settings()
vector_db = VectorDB(settings)
llm = LLM(settings)
cocktail_service = CocktailService(vector_db)
memory_service = MemoryService(vector_db)
rag_service = RAGService(llm, vector_db, cocktail_service, memory_service)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(input_data: ChatInput) -> ChatResponse:
    """
    Process a chat message and return a response
    """
    try:
        # Process the message using RAG service
        response, detected_preferences = rag_service.process_message(
            input_data.message, 
            input_data.session_id
        )
        
        # Return response
        return ChatResponse(
            response=response,
            detected_preferences=detected_preferences.get('favorite_ingredients', []) + 
                                 detected_preferences.get('favorite_cocktails', [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")