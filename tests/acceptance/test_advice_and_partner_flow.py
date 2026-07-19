TEST_AGENT_HEADERS = {"X-Agent-Key-Id": "test-agent-key"}


def test_agent_can_request_recommendation_style_advice_for_compass(client):
    goal_response = client.post(
        "/api/v1/goals",
        json={
            "goal_id": "sg-computer-club",
            "title": "Start a computer club",
            "description": "Help young people learn computing through practice.",
            "visibility": "public",
            "user_approved": True,
        },
    )
    assert goal_response.status_code == 201

    contract_response = client.post(
        "/api/v1/goals/sg-computer-club/contracts",
        headers=TEST_AGENT_HEADERS,
        json={"cadence": "weekly", "time_minutes": 60, "user_approved": True},
    )
    assert contract_response.status_code == 201
    contract_id = contract_response.json()["contract_id"]

    commit_response = client.post(
        f"/api/v1/contracts/{contract_id}/commits",
        headers=TEST_AGENT_HEADERS,
        json={
            "time_minutes": 30,
            "done": "Prepared the first learning room plan.",
            "next_step": "Invite two learners to the first coding session.",
            "skill_tag": "mind",
            "is_happy_moment": True,
            "is_public": False,
            "source_ref": "Compass.md#sg-computer-club-room-plan",
            "user_approved": True,
        },
    )
    assert commit_response.status_code == 201

    advice_response = client.get(
        f"/api/v1/contracts/{contract_id}/advice",
        headers=TEST_AGENT_HEADERS,
    )

    assert advice_response.status_code == 200
    advice = advice_response.json()
    assert advice["contract_id"] == contract_id
    assert advice["goal_id"] == "sg-computer-club"
    assert advice["partner_id"] == "computer_club"
    assert advice["source"] == "partner_stub"
    assert advice["subscription_required"] is False
    assert advice["recommended_next_steps"] == [
        "Invite two learners to the first coding session."
    ]
    assert "recommend" in advice["advice_text"].lower()
    assert "must" not in advice["advice_text"].lower()
    assert "private_source_text" not in advice