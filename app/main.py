from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Union

from app.models.schemas import ChatRequest, ChatResponse, BattleResponse, PokemonData, BattleVisualizationResponse
from app.graph.agent_graph import process_question

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the FastAPI app
app = FastAPI(
    title="Pokémon Multi-Agent System",
    description="A multi-agent system for answering questions about Pokémon",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


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
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )


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
            raise ValueError("Missing winner or reasoning data")

        return BattleResponse(winner=winner.capitalize(), reasoning=reasoning)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing battle: {str(e)}"
        )


@app.get("/battle/visualize", response_model=BattleVisualizationResponse)
async def visualize_battle(pokemon1: str, pokemon2: str, use_shiny: bool = False):
    """
    Generate a visual representation of a Pokémon battle

    Args:
        pokemon1: Name of the first Pokémon
        pokemon2: Name of the second Pokémon
        use_shiny: Whether to use shiny Pokémon sprites (default: False)

    Returns:
        BattleVisualizationResponse with the path to the visualization and metadata
    """
    try:
        # First get the battle result
        battle_result = None
        # question = f"Who would win in a battle between {pokemon1} and {pokemon2}?"
        # battle_result = process_question(question)
        # print(f"Battle result: {battle_result}")
        battle_string = f' The battle result is {battle_result}' if battle_result else ''
        # Then request a visualization
        visualization_question = f"Create a visualization of the battle between {pokemon1} and {pokemon2}{' with shiny sprites' if use_shiny else ''}. {battle_string}"
        visualization_response = process_question(visualization_question)
        print(f"Visualization response: {visualization_response}")
        
        if "visualization_path" not in visualization_response:
            print(f"ERROR: Missing visualization_path in response: {visualization_response}")
            # Try to use the mock endpoint as a fallback
            from app.utils.visualization_utils import generate_battle_animation
            from app.agents.visualizer import ensure_complete_pokemon_data
            
            # Mock data for the first Pokémon
            pokemon1_data = {
                "name": pokemon1,
            }
            
            # Mock data for the second Pokémon
            pokemon2_data = {
                "name": pokemon2,
            }
            
            # Ensure we have complete data
            pokemon1_data = ensure_complete_pokemon_data(pokemon1_data)
            pokemon2_data = ensure_complete_pokemon_data(pokemon2_data)
            
            # Use the battle result from the agent
            gif_path = generate_battle_animation(
                pokemon1_data=pokemon1_data,
                pokemon2_data=pokemon2_data,
                battle_result=battle_result,
                use_shiny=use_shiny
            )
            
            visualization_response = {
                "visualization_path": gif_path,
                "description": f"Battle between {pokemon1} and {pokemon2}",
                "battle_highlights": f"The battle between {pokemon1.capitalize()} and {pokemon2.capitalize()} was intense!"
            }
            
        return BattleVisualizationResponse(
            visualization_path=visualization_response["visualization_path"],
            description=visualization_response.get("description", f"Battle between {pokemon1} and {pokemon2}"),
            pokemon1=pokemon1.capitalize(),
            pokemon2=pokemon2.capitalize(),
            winner=visualization_response.get("winner", "Unknown").capitalize(),
            battle_highlights=visualization_response.get("battle_highlights"),
            shiny_used=use_shiny or visualization_response.get("shiny_used", False)
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in visualize_battle: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=500, detail=f"Error generating battle visualization: {str(e)}"
        )


@app.get("/battle/visualize/view/{filename}")
async def view_battle_visualization(filename: str):
    """
    Serve the battle visualization file

    Args:
        filename: Name of the visualization file

    Returns:
        The visualization file
    """
    try:
        file_path = os.path.join(os.environ.get("TEMP_DIR", "/tmp"), filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Visualization file not found")
        
        return FileResponse(file_path)

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Error serving visualization file: {str(e)}"
        )


@app.get("/battle/visualize/mock", response_model=BattleVisualizationResponse)
async def mock_battle_visualization(pokemon1: str = "pikachu", pokemon2: str = "charizard", use_shiny: bool = False):
    """
    Generate a mock battle visualization for testing purposes
    
    This endpoint bypasses the agent system and uses hardcoded data to generate
    battle visualizations, allowing for quick testing of the visualization functionality.

    Args:
        pokemon1: Name of the first Pokémon (default: pikachu)
        pokemon2: Name of the second Pokémon (default: charizard)
        use_shiny: Whether to use shiny Pokémon sprites (default: False)

    Returns:
        BattleVisualizationResponse with the path to the visualization and metadata
    """
    try:
        from app.utils.visualization_utils import generate_battle_animation
        from app.agents.visualizer import ensure_complete_pokemon_data
        
        # Mock data for the first Pokémon
        pokemon1_data = {
            "name": pokemon1,
            # We'll let ensure_complete_pokemon_data fill in the rest from the API
        }
        
        # Mock data for the second Pokémon
        pokemon2_data = {
            "name": pokemon2,
            # We'll let ensure_complete_pokemon_data fill in the rest from the API
        }
        
        # Ensure we have complete data
        pokemon1_data = ensure_complete_pokemon_data(pokemon1_data)
        pokemon2_data = ensure_complete_pokemon_data(pokemon2_data)
        
        # Determine the winner based on a simple rule (for mock purposes)
        # In a real scenario, this would be determined by the battle agent
        p1_total_stats = sum(pokemon1_data["base_stats"].values())
        p2_total_stats = sum(pokemon2_data["base_stats"].values())
        
        if p1_total_stats > p2_total_stats:
            winner = pokemon1
            reasoning = f"{pokemon1.capitalize()} has higher total stats ({p1_total_stats} vs {p2_total_stats})."
        else:
            winner = pokemon2
            reasoning = f"{pokemon2.capitalize()} has higher total stats ({p2_total_stats} vs {p1_total_stats})."
        
        # Mock battle result
        battle_result = {
            "winner": winner,
            "reasoning": reasoning
        }
        
        # Generate the battle animation
        gif_path = generate_battle_animation(
            pokemon1_data=pokemon1_data,
            pokemon2_data=pokemon2_data,
            battle_result=battle_result,
            use_shiny=use_shiny
        )
        
        # Generate battle highlights
        highlights = f"The battle between {pokemon1.capitalize()} and {pokemon2.capitalize()} was intense! "
        
        if "types" in pokemon1_data and "types" in pokemon2_data:
            p1_types = ", ".join(t.capitalize() for t in pokemon1_data["types"])
            p2_types = ", ".join(t.capitalize() for t in pokemon2_data["types"])
            highlights += f"{pokemon1.capitalize()} used its {p1_types} moves while {pokemon2.capitalize()} countered with {p2_types} attacks. "
        
        highlights += f"In the end, {winner.capitalize()} emerged victorious!"
        
        return BattleVisualizationResponse(
            visualization_path=gif_path,
            description=f"Mock battle visualization between {pokemon1.capitalize()} and {pokemon2.capitalize()}",
            pokemon1=pokemon1.capitalize(),
            pokemon2=pokemon2.capitalize(),
            winner=winner.capitalize(),
            battle_highlights=highlights,
            shiny_used=use_shiny
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating mock battle visualization: {str(e)}"
        )


@app.get("/battle-tester")
async def battle_tester():
    """Serve the battle tester HTML page"""
    return FileResponse(os.path.join(os.path.dirname(__file__), "static/battle_tester.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
    )
