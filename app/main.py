from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Union

from app.models.schemas import ChatRequest, ChatResponse, BattleResponse, PokemonData
from app.graph.agent_graph import process_question

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the FastAPI app
app = FastAPI(
    title="Pokémon Multi-Agent System",
    description="A multi-agent system for answering questions about Pokémon",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint for health checks"""
    return {"status": "ok", "message": "Pokémon Multi-Agent System is running"}

@app.post("/chat", response_model=Union[ChatResponse, PokemonData])
async def chat(request: ChatRequest):
    """
    General chat endpoint for answering user questions
    
    Args:
        request: ChatRequest with the user's question
        
    Returns:
        ChatResponse with the answer and optional reasoning
    """
    try:
        # Process the question through the agent graph
        response = process_question(request.question)

        if "name" in response and "base_stats" in response:
            return PokemonData(**response)
        else:
            # Remove winner key if it exists
            response.pop("winner", None)
            return ChatResponse(**response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/battle", response_model=BattleResponse)
async def battle(pokemon1: str, pokemon2: str):
    """
    Pokémon battle simulation endpoint
    
    Args:
        pokemon1: Name of the first Pokémon
        pokemon2: Name of the second Pokémon
        
    Returns:
        BattleResponse with the winner and reasoning
    """
    try:

        question = f"Who would win in a battle between {pokemon1} and {pokemon2}?"
        response = process_question(question)
        
        response.pop("answer", None)

        winner = response.get("winner", "Unknown")
        reasoning = response.get("reasoning", "No reasoning available.")
        if not winner or not reasoning:
            raise HTTPException(status_code=500, detail="Error processing battle response")

        return BattleResponse(
            winner=winner.capitalize(),
            reasoning=reasoning
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing battle: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
