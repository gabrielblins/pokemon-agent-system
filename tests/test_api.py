"""
Tests for the FastAPI endpoints.
"""

from unittest.mock import patch


def test_root_endpoint(test_client):
    """Test the root endpoint for health check."""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "running" in data["message"]


def test_chat_endpoint_battle_query(test_client, mock_process_question):
    """Test the chat endpoint with a battle query."""
    response = test_client.post(
        "/chat", json={"question": "Who would win in a battle, Pikachu or Charizard?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "Charizard" in data["answer"]
    assert "reasoning" in data


def test_chat_endpoint_stats_query(test_client, mock_process_question):
    """Test the chat endpoint with a stats query."""
    response = test_client.post("/chat", json={"question": "What are Pikachu's stats?"})

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"].lower() == "pikachu"
    assert "base_stats" in data
    assert "types" in data
    assert "electric" in data["types"] or "Electric" in data["types"]


def test_chat_endpoint_invalid_request(test_client):
    """Test the chat endpoint with an invalid request body."""
    response = test_client.post("/chat", json={})

    assert response.status_code == 422  # Unprocessable Entity


def test_battle_endpoint_success(test_client, mock_process_question):
    """Test the battle endpoint with valid Pokémon names."""
    response = test_client.get(
        "/battle", params={"pokemon1": "pikachu", "pokemon2": "charizard"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "winner" in data
    assert data["winner"] == "Charizard"  # Capitalized in the response
    assert "reasoning" in data


def test_battle_endpoint_error_handling(test_client):
    """Test error handling in the battle endpoint."""
    # Using a context manager to limit the scope of the patch and avoid conflict with fixtures
    with patch("app.main.process_question", side_effect=Exception("Test error")):
        response = test_client.get(
            "/battle", params={"pokemon1": "pikachu", "pokemon2": "charizard"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error" in data["detail"]
