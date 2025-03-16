from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., description="User's question")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Answer to the user's question")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the answer")


class PokemonStats(BaseModel):
    """Model for Pokémon base stats"""
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


class PokemonData(BaseModel):
    """Model for Pokémon data"""
    name: str
    base_stats: PokemonStats
    types: List[str] = Field(..., description="List of Pokémon types")


class BattleResponse(BaseModel):
    """Response model for battle endpoint"""
    winner: str = Field(..., description="Name of the winning Pokémon")
    reasoning: str = Field(..., description="Reasoning behind the battle outcome")
