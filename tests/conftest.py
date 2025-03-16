"""
Simplified test fixtures for the Pokémon Multi-Agent System tests.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app


@pytest.fixture
def test_client():
    """Create a FastAPI test client for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_pokemon_data():
    """Mock Pokémon data for testing."""
    return {
        "pikachu": {
            "name": "pikachu",
            "base_stats": {
                "hp": 35,
                "attack": 55,
                "defense": 40,
                "special_attack": 50,
                "special_defense": 50,
                "speed": 90,
            },
            "types": ["electric"],
        },
        "charizard": {
            "name": "charizard",
            "base_stats": {
                "hp": 78,
                "attack": 84,
                "defense": 78,
                "special_attack": 109,
                "special_defense": 85,
                "speed": 100,
            },
            "types": ["fire", "flying"],
        },
    }


@pytest.fixture
def mock_fetch_pokemon_data(mock_pokemon_data):
    """Mock the fetch_pokemon_data function."""

    def _mock_fetch(pokemon_name):
        pokemon_name = pokemon_name.lower()
        if pokemon_name in mock_pokemon_data:
            return mock_pokemon_data[pokemon_name]
        else:
            return {"error": f"Pokémon '{pokemon_name}' not found."}

    with patch("app.utils.pokemon_utils.fetch_pokemon_data", side_effect=_mock_fetch):
        yield


@pytest.fixture
def mock_process_question():
    """Mock the process_question function."""

    def _get_mock_response(question):
        if (
            "battle" in question.lower()
            and "pikachu" in question.lower()
            and "charizard" in question.lower()
        ):
            return {
                "answer": "Charizard would likely win in a battle against Pikachu.",
                "winner": "charizard",
                "reasoning": "Charizard has higher base stats overall.",
            }
        elif "stats" in question.lower() and "pikachu" in question.lower():
            return {
                "name": "pikachu",
                "base_stats": {
                    "hp": 35,
                    "attack": 55,
                    "defense": 40,
                    "special_attack": 50,
                    "special_defense": 50,
                    "speed": 90,
                },
                "types": ["electric"],
            }
        else:
            return {
                "answer": "I don't have enough information to answer that question."
            }

    with patch(
        "app.graph.agent_graph.process_question", side_effect=_get_mock_response
    ):
        yield


@pytest.fixture
def mock_requests_get():
    """Mock the requests.get function."""

    def _mock_requests_get(url):
        # Extract the Pokémon name from the URL
        pokemon_name = url.split("/")[-1].lower()

        mock_responses = {
            "pikachu": {
                "name": "pikachu",
                "stats": [
                    {"base_stat": 35, "stat": {"name": "hp"}},
                    {"base_stat": 55, "stat": {"name": "attack"}},
                    {"base_stat": 40, "stat": {"name": "defense"}},
                    {"base_stat": 50, "stat": {"name": "special-attack"}},
                    {"base_stat": 50, "stat": {"name": "special-defense"}},
                    {"base_stat": 90, "stat": {"name": "speed"}},
                ],
                "types": [{"type": {"name": "electric"}}],
            },
            "charizard": {
                "name": "charizard",
                "stats": [
                    {"base_stat": 78, "stat": {"name": "hp"}},
                    {"base_stat": 84, "stat": {"name": "attack"}},
                    {"base_stat": 78, "stat": {"name": "defense"}},
                    {"base_stat": 109, "stat": {"name": "special-attack"}},
                    {"base_stat": 85, "stat": {"name": "special-defense"}},
                    {"base_stat": 100, "stat": {"name": "speed"}},
                ],
                "types": [{"type": {"name": "fire"}}, {"type": {"name": "flying"}}],
            },
        }

        mock_response = MagicMock()

        if pokemon_name in mock_responses:
            mock_response.status_code = 200
            mock_response.json.return_value = mock_responses[pokemon_name]
        else:
            mock_response.status_code = 404
            mock_response.json.return_value = {"detail": "Not found"}

        return mock_response

    with patch("requests.get", side_effect=_mock_requests_get):
        yield


@pytest.fixture
def mock_llm():
    """Mock for LLM models."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="This is a mock LLM response")

    with (
        patch("langchain_openai.ChatOpenAI", return_value=mock),
        patch("langchain_groq.ChatGroq", return_value=mock),
    ):
        yield mock
