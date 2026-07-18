from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, create_engine, or_, select
from sqlalchemy.orm import Session, sessionmaker

from shared_goals_instance.models import Base, Goal


class GoalCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    visibility: Literal["public", "invite", "personal"]
    instance_id: str = "default"


def create_app(database_url: str = "sqlite:///shared_goals.db") -> FastAPI:
    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    engine = create_engine(database_url, connect_args=connect_args)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title="Shared Goals Instance")

    def get_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    @app.get("/api/v1/goals")
    def list_goals(
        query: str | None = Query(default=None),
        session: Session = Depends(get_session),
    ) -> dict[str, list[dict[str, object]]]:
        statement: Select[tuple[Goal]] = select(Goal)
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(Goal.title.ilike(pattern), Goal.description.ilike(pattern))
            )
        goals = session.scalars(statement.order_by(Goal.created_at)).all()
        return {"goals": [_goal_response(goal) for goal in goals]}

    @app.post("/api/v1/goals", status_code=201)
    def create_goal(
        payload: GoalCreate,
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        moderation_status = _moderation_status(payload)
        goal = Goal(
            id=str(uuid4()),
            title=payload.title,
            description=payload.description,
            visibility=payload.visibility,
            instance_id=payload.instance_id,
            moderation_status=moderation_status,
            created_at=datetime.now(UTC),
        )
        session.add(goal)
        session.commit()
        return _goal_response(goal)

    return app


def _moderation_status(payload: GoalCreate) -> str:
    text = f"{payload.title} {payload.description}".lower()
    competitive_terms = ("beat everyone", "rank people", "ranking", "competition")
    is_competitive = any(term in text for term in competitive_terms)
    if payload.visibility == "public" and is_competitive:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "public_goal_rejected",
                "reason": "competitive public goals are outside MVP scope",
            },
        )
    return "approved"


def _goal_response(goal: Goal) -> dict[str, object]:
    return {
        "goal_id": goal.id,
        "title": goal.title,
        "description": goal.description,
        "visibility": goal.visibility,
        "instance_id": goal.instance_id,
        "moderation_status": goal.moderation_status,
        "created_at": goal.created_at.isoformat(),
    }
