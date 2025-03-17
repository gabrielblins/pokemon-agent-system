#!/usr/bin/env python3
"""
Mock Battle Visualization Generator

This script generates battle visualizations without needing to start the full API server.
It can be run directly from the command line.

Usage:
    python -m app.utils.mock_battle --pokemon1 pikachu --pokemon2 charizard --shiny

    or

    python -m app.utils.mock_battle -p1 pikachu -p2 charizard -s
"""

import argparse
import os
import sys
from typing import Dict, Any

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.utils.visualization_utils import generate_battle_animation
from app.agents.visualizer import ensure_complete_pokemon_data


def generate_mock_battle(pokemon1: str, pokemon2: str, use_shiny: bool = False) -> str:
    """
    Generate a mock battle visualization
    
    Args:
        pokemon1: Name of the first Pokémon
        pokemon2: Name of the second Pokémon
        use_shiny: Whether to use shiny Pokémon sprites
        
    Returns:
        Path to the generated GIF
    """
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
    
    # Determine the winner based on a simple rule (for mock purposes)
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
    
    return gif_path


def main():
    """Main function to parse arguments and generate the battle visualization"""
    parser = argparse.ArgumentParser(description="Generate a mock Pokémon battle visualization")
    parser.add_argument("--pokemon1", "-p1", type=str, default="pikachu", help="Name of the first Pokémon")
    parser.add_argument("--pokemon2", "-p2", type=str, default="charizard", help="Name of the second Pokémon")
    parser.add_argument("--shiny", "-s", action="store_true", help="Use shiny Pokémon sprites")
    
    args = parser.parse_args()
    
    print(f"Generating battle visualization for {args.pokemon1.capitalize()} vs {args.pokemon2.capitalize()}...")
    print(f"Using {'shiny' if args.shiny else 'regular'} sprites")
    
    try:
        gif_path = generate_mock_battle(args.pokemon1, args.pokemon2, args.shiny)
        print(f"Battle visualization generated successfully!")
        print(f"GIF saved to: {gif_path}")
        
        # Try to open the GIF with the default image viewer
        try:
            if sys.platform == "win32":
                os.startfile(gif_path)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open {gif_path}")
            else:  # Linux
                os.system(f"xdg-open {gif_path}")
        except Exception as e:
            print(f"Could not open the GIF automatically: {str(e)}")
            
    except Exception as e:
        print(f"Error generating battle visualization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 