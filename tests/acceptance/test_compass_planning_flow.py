TEST_AGENT_HEADERS = {"X-Agent-Key-Id": "test-agent-key"}


def test_agent_can_list_joined_contracts_for_compass_planning(client):
    goal_response = client.post(
        "/api/v1/goals",
        json={
            "goal_id": "sg-oss-coding",
            "title": "Contribute to open source together",
            "description": "Build public software through steady shared practice.",
            "visibility": "public",
            "user_approved": True,
        },
    )
    assert goal_response.status_code == 201
    assert goal_response.json()["goal_id"] == "sg-oss-coding"

    contract_response = client.post(
        "/api/v1/goals/sg-oss-coding/contracts",
        headers=TEST_AGENT_HEADERS,
        json={"cadence": "weekly", "time_minutes": 45, "user_approved": True},
    )
    assert contract_response.status_code == 201
    contract_id = contract_response.json()["contract_id"]

    response = client.get("/api/v1/contracts", headers=TEST_AGENT_HEADERS)

    assert response.status_code == 200
    contracts = response.json()["contracts"]
    assert contracts == [
        {
            "contract_id": contract_id,
            "goal_id": "sg-oss-coding",
            "goal_tag": "#sg-oss-coding",
            "goal_title": "Contribute to open source together",
            "cadence": "weekly",
            "time_minutes": 45,
            "is_active": True,
            "latest_next_step": None,
        }
    ]
    assert "private_source_text" not in contracts[0]