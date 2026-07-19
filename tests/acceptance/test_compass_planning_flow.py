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


def test_agent_can_fetch_platform_compass_next_steps(client):
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
            "time_minutes": 30,
            "done": "Reviewed the first platform Compass slice.",
            "next_step": "Replace one local Compass registry read with the API feed.",
            "skill_tag": "mind",
            "is_happy_moment": True,
            "is_public": False,
            "source_ref": "Compass.md#sg-oss-coding-api-feed",
            "user_approved": True,
        },
    )
    assert commit_response.status_code == 201

    response = client.get("/api/v1/compass/next-steps", headers=TEST_AGENT_HEADERS)

    assert response.status_code == 200
    assert response.json() == {
        "next_steps": [
            {
                "contract_id": contract_id,
                "goal_id": "sg-oss-coding",
                "goal_tag": "#sg-oss-coding",
                "goal_title": "Contribute to open source together",
                "next_step": (
                    "Replace one local Compass registry read with the API feed."
                ),
                "cadence": "weekly",
                "time_minutes": 45,
                "skill_tag": "mind",
                "is_happy_moment": True,
                "source": "platform",
            }
        ]
    }
    assert "private_source_text" not in response.json()["next_steps"][0]