"""
Basic tests for the agent components.
"""

from unittest.mock import patch, MagicMock
from app.agents.researcher import fetch_pokemon_info
from app.agents.pokemon_expert import analyze_battle
from app.agents.supervisor import format_response, check_json


def test_fetch_pokemon_info(mock_fetch_pokemon_data, mock_pokemon_data):
    """Test fetch_pokemon_info from the Researcher Agent."""
    result = fetch_pokemon_info("pikachu")

    assert result == mock_pokemon_data["pikachu"]

    # Test with an invalid name
    result = fetch_pokemon_info("notapokemon")
    assert "error" in result


@patch("app.utils.pokemon_utils.analyze_pokemon_battle")
def test_analyze_battle(mock_analyze_battle, mock_pokemon_data):
    """Test analyze_battle from the Expert Agent."""
    # Set up mock return value
    mock_analyze_battle.return_value = (
        "charizard",
        "Charizard has higher stats and would win.",
    )

    winner, reasoning = analyze_battle(
        mock_pokemon_data["pikachu"], mock_pokemon_data["charizard"]
    )

    reasoning = reasoning.lower()

    possible_reasons = [
        "higher stats",
        "type advantage",
        "would win",
        "faster",
        "stronger",
        "more powerful",
        "more effective",
        "super effective",
        "better stats",
        "not very effective",
        "effective",
        "not effective",
        "weakness",
        "resistant",
    ]

    assert winner == "charizard"
    assert any(reason in reasoning for reason in possible_reasons)


def test_check_json():
    """Test check_json from the Supervisor Agent."""
    # Test with a JSON code block
    text = """Here is the answer:
    ```json
    {
        "answer": "Pikachu is an Electric-type Pokémon"
    }
    ```"""

    result = check_json(text)

    assert isinstance(result, dict)
    assert result["answer"] == "Pikachu is an Electric-type Pokémon"

    # Test with raw JSON
    text = """{"answer": "Charizard is a Fire/Flying type"}"""

    result = check_json(text)

    assert isinstance(result, dict)
    assert result["answer"] == "Charizard is a Fire/Flying type"

    # Test with non-JSON
    text = "This is not JSON"

    result = check_json(text)

    assert result == {}


@patch("app.agents.supervisor.ChatOpenAI")
def test_format_response(mock_chat_model):
    """Test format_response from the Supervisor Agent."""
    # Set up with text that already contains JSON
    text = """```json
    {
        "answer": "Pikachu is an Electric-type Pokémon"
    }
    ```"""

    with patch("os.getenv", return_value="openai"):
        result = format_response(text)

    assert isinstance(result, dict)
    assert result["answer"] == "Pikachu is an Electric-type Pokémon"


@patch("app.graph.agent_graph.create_agent_graph")
def test_process_question(mock_create_agent_graph):
    """Test the process_question function."""
    from app.graph.agent_graph import process_question

    # Set up the mock graph
    mock_graph = MagicMock()
    mock_create_agent_graph.return_value = mock_graph

    # Set up the mock state
    mock_state = {
        "messages": [
            ("user", "Who would win in a battle, Pikachu or Charizard?"),
            (
                "agent",
                """```json
            {
                "answer": "Charizard would likely win in a battle against Pikachu.",
                "winner": "charizard",
                "reasoning": "Charizard has higher base stats overall."
            }
            ```""",
            ),
        ]
    }

    mock_graph.invoke.return_value = mock_state

    # Call the function
    with patch("builtins.open", MagicMock()):  # Mock file operations
        result = process_question("Who would win in a battle, Pikachu or Charizard?")

    # Verify the result
    assert isinstance(result, dict)
    assert "answer" in result
    assert "winner" in result
    assert result["winner"].lower() == "charizard"
