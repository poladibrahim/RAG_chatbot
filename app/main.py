from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

from app.core.config_settings import Settings
from app.api import chat, memory
from app.services.cocktail import CocktailService
from app.services.memory import MemoryService
from app.services.rag import RAGService
from app.core.vector_db import VectorDB
from app.core.llm import LLM

# Load environment variables
load_dotenv()

# Initialize app
app = FastAPI(title="Cocktail Advisor Chat")

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Set up templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Initialize services
settings = Settings()
vector_db = VectorDB(settings)
llm = LLM(settings)
cocktail_service = CocktailService(vector_db)
memory_service = MemoryService(vector_db)
rag_service = RAGService(llm, vector_db, cocktail_service, memory_service)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(memory.router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.on_event("startup")
async def startup_event():
    # Ensure vector database is initialized
    vector_db.initialize()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)