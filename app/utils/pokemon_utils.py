import requests
from typing import Dict, List, Tuple, Any

# Type effectiveness chart - a mapping of attacking type to a list of types it's super effective against
TYPE_ADVANTAGES = {
    "normal": [],
    "fire": ["grass", "ice", "bug", "steel"],
    "water": ["fire", "ground", "rock"],
    "electric": ["water", "flying"],
    "grass": ["water", "ground", "rock"],
    "ice": ["grass", "ground", "flying", "dragon"],
    "fighting": ["normal", "ice", "rock", "dark", "steel"],
    "poison": ["grass", "fairy"],
    "ground": ["fire", "electric", "poison", "rock", "steel"],
    "flying": ["grass", "fighting", "bug"],
    "psychic": ["fighting", "poison"],
    "bug": ["grass", "psychic", "dark"],
    "rock": ["fire", "ice", "flying", "bug"],
    "ghost": ["psychic", "ghost"],
    "dragon": ["dragon"],
    "dark": ["psychic", "ghost"],
    "steel": ["ice", "rock", "fairy"],
    "fairy": ["fighting", "dragon", "dark"]
}

# Type immunities - a mapping of attacking type to a list of types that are immune to it
TYPE_IMMUNITIES = {
    "normal": ["ghost"],
    "electric": ["ground"],
    "fighting": ["ghost"],
    "poison": ["steel"],
    "ground": ["flying"],
    "psychic": ["dark"],
    "ghost": ["normal"],
    "dragon": ["fairy"]
}

# Fetch Pokémon data from PokéAPI
def fetch_pokemon_data(pokemon_name: str) -> Dict[str, Any]:
    """
    Fetch Pokémon data from PokéAPI
    
    Args:
        pokemon_name: Name of the Pokémon (lowercase)
        
    Returns:
        Dictionary containing Pokémon data
    """
    # Clean the pokemon name (lowercase, remove spaces and special characters)
    clean_name = pokemon_name.lower().strip()
    
    # Make API request
    response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{clean_name}")
    
    # Check if the request was successful
    if response.status_code == 200:
        
        # check if the response is Not Found

        
        data = response.json()
        
        # Extract relevant information
        pokemon_info = {
            "name": data["name"],
            "base_stats": {
                "hp": data["stats"][0]["base_stat"],
                "attack": data["stats"][1]["base_stat"],
                "defense": data["stats"][2]["base_stat"],
                "special_attack": data["stats"][3]["base_stat"],
                "special_defense": data["stats"][4]["base_stat"],
                "speed": data["stats"][5]["base_stat"]
            },
            "types": [t["type"]["name"] for t in data["types"]]
        }
        
        return pokemon_info
    else:
        return {
            "error": f"Pokémon '{pokemon_name}' not found."
        }

def calculate_type_effectiveness(attacker_types: List[str], defender_types: List[str]) -> float:
    """
    Calculate type effectiveness multiplier for an attack
    
    Args:
        attacker_types: List of the attacker's types
        defender_types: List of the defender's types
        
    Returns:
        Effectiveness multiplier (0, 0.5, 1, 2, or 4)
    """
    # Default effectiveness is neutral (1x)
    effectiveness = 1.0
    
    for attacker_type in attacker_types:
        # Check for immunities first
        if attacker_type in TYPE_IMMUNITIES:
            if any(dtype in TYPE_IMMUNITIES[attacker_type] for dtype in defender_types):
                return 0.0  # Immune, no damage
        
        # Check for super effectiveness
        if attacker_type in TYPE_ADVANTAGES:
            for defender_type in defender_types:
                if defender_type in TYPE_ADVANTAGES[attacker_type]:
                    effectiveness *= 2.0  # Super effective
    
    return effectiveness


def analyze_pokemon_battle(pokemon1: Dict[str, Any], pokemon2: Dict[str, Any]) -> Tuple[str, str]:
    """
    Analyze a battle between two Pokémon and determine the likely winner
    
    Args:
        pokemon1: Data for the first Pokémon
        pokemon2: Data for the second Pokémon
        
    Returns:
        Tuple containing (winner name, reasoning)
    """
    # Calculate type effectiveness in both directions
    p1_type_effectiveness = calculate_type_effectiveness(pokemon1["types"], pokemon2["types"])
    print(f"Type effectiveness for {pokemon1['name']}: {p1_type_effectiveness}")
    p2_type_effectiveness = calculate_type_effectiveness(pokemon2["types"], pokemon1["types"])
    print(f"Type effectiveness for {pokemon2['name']}: {p2_type_effectiveness}")
    
    # Calculate a simple battle score based on stats and type effectiveness
    p1_attack = pokemon1["base_stats"]["attack"] * p1_type_effectiveness
    p1_sp_attack = pokemon1["base_stats"]["special_attack"] * p1_type_effectiveness
    p1_attack_power = max(p1_attack, p1_sp_attack)
    
    p2_attack = pokemon2["base_stats"]["attack"] * p2_type_effectiveness
    p2_sp_attack = pokemon2["base_stats"]["special_attack"] * p2_type_effectiveness
    p2_attack_power = max(p2_attack, p2_sp_attack)
    
    # Calculate effective HP (HP * defense or special defense)
    p1_defense = (pokemon1["base_stats"]["defense"] + pokemon1["base_stats"]["special_defense"]) / 2
    p2_defense = (pokemon2["base_stats"]["defense"] + pokemon2["base_stats"]["special_defense"]) / 2
    
    p1_effective_hp = pokemon1["base_stats"]["hp"] * (p1_defense / 100)
    p2_effective_hp = pokemon2["base_stats"]["hp"] * (p2_defense / 100)
    
    # Approximate number of turns to defeat opponent
    p1_turns_to_win = p2_effective_hp / max(p1_attack_power, 1)
    p2_turns_to_win = p1_effective_hp / max(p2_attack_power, 1)
    
    # Speed advantage (who attacks first)
    p1_speed = pokemon1["base_stats"]["speed"]
    p2_speed = pokemon2["base_stats"]["speed"]
    
    # Determine the winner
    reasoning_factors = []
    
    # Type advantage reasoning
    if p1_type_effectiveness > p2_type_effectiveness:
        reasoning_factors.append(f"{pokemon1['name'].capitalize()} has a type advantage over {pokemon2['name'].capitalize()}")
    elif p2_type_effectiveness > p1_type_effectiveness:
        reasoning_factors.append(f"{pokemon2['name'].capitalize()} has a type advantage over {pokemon1['name'].capitalize()}")
    else:
        reasoning_factors.append("Neither Pokémon has a significant type advantage")
    
    # Speed reasoning
    if p1_speed > p2_speed:
        reasoning_factors.append(f"{pokemon1['name'].capitalize()} is faster and would attack first")
    elif p2_speed > p1_speed:
        reasoning_factors.append(f"{pokemon2['name'].capitalize()} is faster and would attack first")
    
    # Attack power reasoning
    if p1_attack_power > p2_attack_power:
        reasoning_factors.append(f"{pokemon1['name'].capitalize()} has stronger attacking moves")
    elif p2_attack_power > p1_attack_power:
        reasoning_factors.append(f"{pokemon2['name'].capitalize()} has stronger attacking moves")
    
    # Make the final determination
    # Lower turns to win is better
    if p1_turns_to_win < p2_turns_to_win:
        winner = pokemon1["name"]
    elif p2_turns_to_win < p1_turns_to_win:
        winner = pokemon2["name"]
    # If turns to win are equal, the faster Pokémon wins
    elif p1_speed > p2_speed:
        winner = pokemon1["name"]
    elif p2_speed > p1_speed:
        winner = pokemon2["name"]
    # If everything is equal, the one with higher HP wins
    elif pokemon1["base_stats"]["hp"] > pokemon2["base_stats"]["hp"]:
        winner = pokemon1["name"]
    else:
        winner = pokemon2["name"]
    
    # Create reasoning string
    reasoning = ". ".join(reasoning_factors) + "."
    
    return winner, reasoning
