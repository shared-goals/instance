def test_agent_can_create_and_find_public_goal(client):
    create_response = client.post(
        "/api/v1/goals",
        json={
            "title": "Start a computer club",
            "description": (
                "Help young people learn computing through regular practice."
            ),
            "visibility": "public",
            "user_approved": True,
        },
    )

    assert create_response.status_code == 201
    created_goal = create_response.json()
    assert created_goal["goal_id"]
    assert created_goal["title"] == "Start a computer club"
    assert created_goal["visibility"] == "public"
    assert created_goal["instance_id"] == "default"
    assert created_goal["moderation_status"] == "approved"
    assert created_goal["created_at"]

    search_response = client.get("/api/v1/goals", params={"query": "computer"})

    assert search_response.status_code == 200
    goals = search_response.json()["goals"]
    assert [goal["goal_id"] for goal in goals] == [created_goal["goal_id"]]
    assert "private_source_text" not in goals[0]


def test_public_competitive_goal_is_rejected(client):
    response = client.post(
        "/api/v1/goals",
        json={
            "title": "Beat everyone in the city",
            "description": "A public competition to rank people by wins.",
            "visibility": "public",
            "user_approved": True,
        },
    )

    assert response.status_code == 422
    error = response.json()
    assert error["detail"]["code"] == "public_goal_rejected"
    assert "competitive" in error["detail"]["reason"]


def test_unapproved_goal_creation_is_rejected(client):
    response = client.post(
        "/api/v1/goals",
        json={
            "title": "Practice music together",
            "description": "Build a shared music practice habit.",
            "visibility": "public",
            "user_approved": False,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "user_approval_required"
