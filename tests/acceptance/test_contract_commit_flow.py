TEST_AGENT_HEADERS = {"X-Agent-Key-Id": "test-agent-key"}
TEST_USER_ID = "00000000-0000-4000-8000-000000000001"


def test_agent_can_join_goal_with_contract_and_reduce_time(client):
    goal_response = client.post(
        "/api/v1/goals",
        json={
            "title": "Practice programming together",
            "description": "Build a steady computer club practice habit.",
            "visibility": "public",
            "user_approved": True,
        },
    )
    goal_id = goal_response.json()["goal_id"]

    contract_response = client.post(
        f"/api/v1/goals/{goal_id}/contracts",
        headers=TEST_AGENT_HEADERS,
        json={"cadence": "weekly", "time_minutes": 60, "user_approved": True},
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
        json={"time_minutes": 30, "user_approved": True},
    )

    assert reduced_response.status_code == 200
    reduced_contract = reduced_response.json()
    assert reduced_contract["contract_id"] == contract["contract_id"]
    assert reduced_contract["time_minutes"] == 30
    assert reduced_contract["is_active"] is True


def test_agent_can_log_compass_commit_against_contract(client):
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

    contract_response = client.post(
        "/api/v1/goals/sg-oss-coding/contracts",
        headers=TEST_AGENT_HEADERS,
        json={"cadence": "weekly", "time_minutes": 45, "user_approved": True},
    )
    assert contract_response.status_code == 201
    contract_id = contract_response.json()["contract_id"]

    commit_response = client.post(
        f"/api/v1/contracts/{contract_id}/commits",
        headers=TEST_AGENT_HEADERS,
        json={
            "time_minutes": 45,
            "done": "Completed the first Compass coding step.",
            "next_step": "Submit the first small patch.",
            "skill_tag": "mind",
            "is_happy_moment": True,
            "is_public": False,
            "source_ref": "Compass.md#sg-oss-coding-first-step",
            "user_approved": True,
        },
    )

    assert commit_response.status_code == 201
    commit = commit_response.json()
    assert commit["commit_id"]
    assert commit["contract_id"] == contract_id
    assert commit["time_minutes"] == 45
    assert commit["done"] == "Completed the first Compass coding step."
    assert commit["next_step"] == "Submit the first small patch."
    assert commit["skill_tag"] == "mind"
    assert commit["is_happy_moment"] is True
    assert commit["is_public"] is False
    assert commit["created_at"]
    assert "source_ref" not in commit

    contracts_response = client.get("/api/v1/contracts", headers=TEST_AGENT_HEADERS)

    assert contracts_response.status_code == 200
    contracts = contracts_response.json()["contracts"]
    assert contracts[0]["latest_next_step"] == "Submit the first small patch."
