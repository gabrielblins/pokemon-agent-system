from typing import List, Optional
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


class BattleVisualizationResponse(BaseModel):
    """Response model for battle visualization endpoint"""

    visualization_path: str = Field(..., description="Path to the visualization file")
    description: str = Field(..., description="Description of the visualization")
    pokemon1: str = Field(..., description="Name of the first Pokémon")
    pokemon2: str = Field(..., description="Name of the second Pokémon")
    winner: str = Field(..., description="Name of the winning Pokémon")
    battle_highlights: Optional[str] = Field(None, description="Brief highlights of key moments in the battle")
    shiny_used: Optional[bool] = Field(False, description="Whether shiny Pokémon sprites were used")
