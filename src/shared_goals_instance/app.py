from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, create_engine, or_, select
from sqlalchemy.orm import Session, sessionmaker

from shared_goals_instance.models import Base, Commit, Contract, Goal

TEST_AGENT_KEY_ID = "test-agent-key"
TEST_USER_ID = "00000000-0000-4000-8000-000000000001"


class GoalCreate(BaseModel):
    goal_id: str | None = Field(default=None, min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    visibility: Literal["public", "invite", "personal"]
    instance_id: str = "default"
    user_approved: bool


class ContractCreate(BaseModel):
    cadence: Literal["daily", "weekly", "monthly", "occasionally"]
    time_minutes: int | None = Field(default=None, ge=0)
    user_approved: bool


class ContractUpdate(BaseModel):
    time_minutes: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    user_approved: bool


class CommitCreate(BaseModel):
    time_minutes: int | None = Field(default=None, ge=0)
    done: str | None = None
    next_step: str | None = None
    skill_tag: Literal["will", "mind", "feeling", "faith"] | None = None
    is_happy_moment: bool = False
    is_public: bool = False
    source_ref: str | None = None
    user_approved: bool


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
        _require_user_approval(payload.user_approved)
        moderation_status = _moderation_status(payload)
        goal = Goal(
            id=_goal_id(payload.goal_id),
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

    @app.get("/api/v1/contracts")
    def list_contracts(
        user_id: str = Depends(_user_id_from_agent_key),
        session: Session = Depends(get_session),
    ) -> dict[str, list[dict[str, object]]]:
        statement = (
            select(Contract, Goal)
            .join(Goal, Contract.goal_id == Goal.id)
            .where(Contract.user_id == user_id, Contract.is_active.is_(True))
            .order_by(Contract.created_at)
        )
        rows = session.execute(statement).all()
        return {
            "contracts": [
                _compass_contract_response(contract, goal, session)
                for contract, goal in rows
            ]
        }

    @app.post("/api/v1/goals/{goal_id}/contracts", status_code=201)
    def create_contract(
        goal_id: str,
        payload: ContractCreate,
        user_id: str = Depends(_user_id_from_agent_key),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        _require_user_approval(payload.user_approved)
        goal = session.get(Goal, goal_id)
        if goal is None:
            raise HTTPException(status_code=404, detail={"code": "goal_not_found"})

        contract = Contract(
            id=str(uuid4()),
            goal_id=goal.id,
            user_id=user_id,
            cadence=payload.cadence,
            time_minutes=payload.time_minutes,
            is_active=True,
            created_at=datetime.now(UTC),
        )
        session.add(contract)
        session.commit()
        return _contract_response(contract)

    @app.patch("/api/v1/contracts/{contract_id}")
    def update_contract(
        contract_id: str,
        payload: ContractUpdate,
        user_id: str = Depends(_user_id_from_agent_key),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        _require_user_approval(payload.user_approved)
        contract = session.get(Contract, contract_id)
        if contract is None or contract.user_id != user_id:
            raise HTTPException(status_code=404, detail={"code": "contract_not_found"})

        if "time_minutes" in payload.model_fields_set:
            _apply_time_reduction(contract, payload.time_minutes)
        if payload.is_active is not None:
            contract.is_active = payload.is_active

        session.commit()
        return _contract_response(contract)

    @app.post("/api/v1/contracts/{contract_id}/commits", status_code=201)
    def create_commit(
        contract_id: str,
        payload: CommitCreate,
        user_id: str = Depends(_user_id_from_agent_key),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        _require_user_approval(payload.user_approved)
        contract = _contract_for_user(session, contract_id, user_id)
        done = payload.done or _latest_next_step(session, contract.id)
        commit = Commit(
            id=str(uuid4()),
            contract_id=contract.id,
            time_minutes=payload.time_minutes,
            done=done,
            next_step=payload.next_step,
            skill_tag=payload.skill_tag,
            is_happy_moment=payload.is_happy_moment,
            is_public=payload.is_public,
            source_ref=payload.source_ref,
            created_at=datetime.now(UTC),
        )
        session.add(commit)
        session.commit()
        return _commit_response(commit)

    @app.get("/api/v1/contracts/{contract_id}/advice")
    def get_contract_advice(
        contract_id: str,
        user_id: str = Depends(_user_id_from_agent_key),
        session: Session = Depends(get_session),
    ) -> dict[str, object]:
        contract = _contract_for_user(session, contract_id, user_id)
        goal = session.get(Goal, contract.goal_id)
        if goal is None:
            raise HTTPException(status_code=404, detail={"code": "goal_not_found"})

        partner_id = _partner_id(goal)
        latest_next_step = _latest_next_step(session, contract.id)
        recommendations = [latest_next_step] if latest_next_step else []
        return {
            "contract_id": contract.id,
            "goal_id": goal.id,
            "partner_id": partner_id,
            "advice_text": _advice_text(goal, partner_id),
            "recommended_next_steps": recommendations,
            "source": "partner_stub" if partner_id else "platform",
            "subscription_required": False,
        }

    return app


def _user_id_from_agent_key(
    agent_key_id: str = Header(alias="X-Agent-Key-Id"),
) -> str:
    if agent_key_id != TEST_AGENT_KEY_ID:
        raise HTTPException(status_code=401, detail={"code": "invalid_agent_key"})
    return TEST_USER_ID


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


def _require_user_approval(user_approved: bool) -> None:
    if not user_approved:
        raise HTTPException(status_code=422, detail={"code": "user_approval_required"})


def _goal_id(goal_id: str | None) -> str:
    if goal_id is None:
        return str(uuid4())
    normalized = goal_id.strip().removeprefix("#")
    if not normalized:
        raise HTTPException(status_code=422, detail={"code": "invalid_goal_id"})
    return normalized


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


def _apply_time_reduction(contract: Contract, time_minutes: int | None) -> None:
    if (
        contract.time_minutes is not None
        and time_minutes is not None
        and time_minutes > contract.time_minutes
    ):
        raise HTTPException(
            status_code=422,
            detail={"code": "contract_time_increase_not_supported"},
        )
    contract.time_minutes = time_minutes


def _contract_response(contract: Contract) -> dict[str, object]:
    return {
        "contract_id": contract.id,
        "goal_id": contract.goal_id,
        "user_id": contract.user_id,
        "cadence": contract.cadence,
        "time_minutes": contract.time_minutes,
        "is_active": contract.is_active,
        "created_at": contract.created_at.isoformat(),
    }


def _compass_contract_response(
    contract: Contract,
    goal: Goal,
    session: Session,
) -> dict[str, object]:
    return {
        "contract_id": contract.id,
        "goal_id": goal.id,
        "goal_tag": f"#{goal.id}",
        "goal_title": goal.title,
        "cadence": contract.cadence,
        "time_minutes": contract.time_minutes,
        "is_active": contract.is_active,
        "latest_next_step": _latest_next_step(session, contract.id),
    }


def _contract_for_user(session: Session, contract_id: str, user_id: str) -> Contract:
    contract = session.get(Contract, contract_id)
    if contract is None or contract.user_id != user_id:
        raise HTTPException(status_code=404, detail={"code": "contract_not_found"})
    return contract


def _latest_next_step(session: Session, contract_id: str) -> str | None:
    statement = (
        select(Commit.next_step)
        .where(Commit.contract_id == contract_id, Commit.next_step.is_not(None))
        .order_by(Commit.created_at.desc())
        .limit(1)
    )
    return session.scalar(statement)


def _partner_id(goal: Goal) -> str | None:
    text = f"{goal.id} {goal.title} {goal.description}".lower()
    if "computer club" in text:
        return "computer_club"
    return None


def _advice_text(goal: Goal, partner_id: str | None) -> str:
    if partner_id == "computer_club":
        return (
            "We recommend choosing one small computer-club step that can fit "
            "this contract period."
        )
    return f"We recommend choosing one small next step for {goal.title}."


def _commit_response(commit: Commit) -> dict[str, object]:
    return {
        "commit_id": commit.id,
        "contract_id": commit.contract_id,
        "time_minutes": commit.time_minutes,
        "done": commit.done,
        "next_step": commit.next_step,
        "skill_tag": commit.skill_tag,
        "is_happy_moment": commit.is_happy_moment,
        "is_public": commit.is_public,
        "created_at": commit.created_at.isoformat(),
    }
