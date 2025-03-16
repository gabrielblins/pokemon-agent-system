"""
Tests for Pokemon utility functions.
"""

from app.utils.pokemon_utils import (
    fetch_pokemon_data,
    calculate_type_effectiveness,
    analyze_pokemon_battle,
)


def test_fetch_pokemon_data_success(mock_requests_get):
    """Test fetch_pokemon_data when the API call is successful."""
    result = fetch_pokemon_data("pikachu")

    assert result["name"] == "pikachu"
    assert "base_stats" in result
    assert "types" in result
    assert result["types"] == ["electric"]
    assert result["base_stats"]["hp"] == 35


def test_fetch_pokemon_data_not_found(mock_requests_get):
    """Test fetch_pokemon_data when the Pokémon is not found."""
    result = fetch_pokemon_data("notapokemon")

    assert "error" in result
    assert "not found" in result["error"]


def test_calculate_type_effectiveness():
    """Test calculation of type effectiveness."""
    # Water is super effective against Fire
    effectiveness = calculate_type_effectiveness(["water"], ["fire"])
    assert effectiveness == 2.0

    # Electric is super effective against Water
    effectiveness = calculate_type_effectiveness(["electric"], ["water"])
    assert effectiveness == 2.0

    # Normal is neutral against Water
    effectiveness = calculate_type_effectiveness(["normal"], ["water"])
    assert effectiveness == 1.0

    # Ground attacks don't affect Flying types
    effectiveness = calculate_type_effectiveness(["ground"], ["flying"])
    assert effectiveness == 0.0


def test_analyze_pokemon_battle(mock_pokemon_data):
    """Test battle analysis between two Pokémon."""
    pikachu = mock_pokemon_data["pikachu"]
    charizard = mock_pokemon_data["charizard"]

    winner, reasoning = analyze_pokemon_battle(pikachu, charizard)

    # Verify that we get a non-empty result
    assert winner in [pikachu["name"], charizard["name"]]
    assert reasoning
    assert len(reasoning) > 10
