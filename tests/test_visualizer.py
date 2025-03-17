import os
import pytest
from unittest.mock import patch, MagicMock
from app.agents.visualizer import create_battle_visualization
from app.utils.visualization_utils import generate_battle_animation


@pytest.fixture
def mock_pokemon_data():
    """Mock Pokémon data for testing"""
    pokemon1_data = {
        "name": "pikachu",
        "base_stats": {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90
        },
        "types": ["electric"]
    }
    
    pokemon2_data = {
        "name": "charizard",
        "base_stats": {
            "hp": 78,
            "attack": 84,
            "defense": 78,
            "special_attack": 109,
            "special_defense": 85,
            "speed": 100
        },
        "types": ["fire", "flying"]
    }
    
    battle_result = {
        "winner": "charizard",
        "reasoning": "Charizard's higher stats and type advantage would likely lead to victory."
    }
    
    return pokemon1_data, pokemon2_data, battle_result


@pytest.mark.parametrize("temp_dir", ["/tmp", "./tmp"])
@patch("app.agents.visualizer.generate_battle_animation")
def test_create_battle_visualization(mock_generate, temp_dir, mock_pokemon_data):
    """Test that battle visualization is created correctly"""
    # Setup
    pokemon1_data, pokemon2_data, battle_result = mock_pokemon_data
    expected_path = os.path.join(temp_dir, "test_battle.gif")
    mock_generate.return_value = expected_path
    
    # Configure environment variable
    os.environ["TEMP_DIR"] = temp_dir
    
    # Execute
    result = create_battle_visualization(pokemon1_data, pokemon2_data, battle_result)
    
    # Verify
    mock_generate.assert_called_once_with(
        pokemon1_data=pokemon1_data,
        pokemon2_data=pokemon2_data,
        battle_result=battle_result,
        use_shiny=False
    )
    
    assert result == expected_path


@patch("app.utils.visualization_utils.imageio.mimsave")
@patch("app.utils.visualization_utils.create_battle_frame")
@patch("app.utils.visualization_utils.get_pokemon_sprite")
def test_generate_battle_animation(mock_get_sprite, mock_create_frame, mock_mimsave, mock_pokemon_data):
    """Test that battle animation is generated correctly"""
    # Setup
    pokemon1_data, pokemon2_data, battle_result = mock_pokemon_data
    mock_sprite = MagicMock()
    mock_frame = MagicMock()
    mock_get_sprite.return_value = mock_sprite
    mock_create_frame.return_value = mock_frame
    
    # Configure environment variable
    os.environ["TEMP_DIR"] = "/tmp"
    
    # Execute
    result = generate_battle_animation(pokemon1_data, pokemon2_data, battle_result)
    
    # Verify
    assert mock_get_sprite.call_count == 2
    assert mock_create_frame.call_count >= 3  # At least initial, final, and some battle frames
    assert mock_mimsave.call_count == 1
    assert os.path.dirname(result) == "/tmp"
    assert result.endswith(".gif") 