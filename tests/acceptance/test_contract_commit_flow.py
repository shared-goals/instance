TEST_AGENT_HEADERS = {"X-Agent-Key-Id": "test-agent-key"}
TEST_USER_ID = "00000000-0000-4000-8000-000000000001"


def test_agent_can_join_goal_with_contract_and_reduce_time(client):
    goal_response = client.post(
        "/api/v1/goals",
        json={
            "title": "Practice programming together",
            "description": "Build a steady computer club practice habit.",
            "visibility": "public",
        },
    )
    goal_id = goal_response.json()["goal_id"]

    contract_response = client.post(
        f"/api/v1/goals/{goal_id}/contracts",
        headers=TEST_AGENT_HEADERS,
        json={"cadence": "weekly", "time_minutes": 60},
    )

    assert contract_response.status_code == 201
    contract = contract_response.json()
    assert contract["contract_id"]
    assert contract["goal_id"] == goal_id
    assert contract["user_id"] == TEST_USER_ID
    assert contract["cadence"] == "weekly"
    assert contract["time_minutes"] == 60
    assert contract["is_active"] is True
    assert contract["created_at"]
    assert "reminder" not in contract
    assert "streak" not in contract
    assert "ranking" not in contract

    reduced_response = client.patch(
        f"/api/v1/contracts/{contract['contract_id']}",
        headers=TEST_AGENT_HEADERS,
        json={"time_minutes": 30},
    )

    assert reduced_response.status_code == 200
    reduced_contract = reduced_response.json()
    assert reduced_contract["contract_id"] == contract["contract_id"]
    assert reduced_contract["time_minutes"] == 30
    assert reduced_contract["is_active"] is True
