from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Agent

router = APIRouter()

_INVITE_CODES = {"AVOS-OPEN-2026", "PARTNER-KEY-01"}


class ExternalRegisterRequest(BaseModel):
    developer_id: str = Field(..., max_length=64)
    bot_name: str = Field(..., max_length=64)
    capabilities: list[str] = Field(default_factory=list)
    invite_code: str = Field(..., min_length=6)


class ExternalRegisterResponse(BaseModel):
    agent_id: str
    public_key: str
    registered_at: datetime


@router.post("/external/register_agent", response_model=ExternalRegisterResponse)
def external_register_agent(
    payload: ExternalRegisterRequest,
    db: Session = Depends(get_db),
):
    """Invite-protected onboarding endpoint for OpenClaw bots.

    OpenClaw agents should call this over HTTPS (or via `ngrok http 8000` for local dev)
    with `developer_id`, `bot_name`, capabilities list, and a shared `invite_code`.
    """
    if payload.invite_code not in _INVITE_CODES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid invite code",
        )
    agent = Agent(
        agent_id=str(uuid4()),
        name=payload.bot_name,
        owner_id=payload.developer_id,
        capabilities=payload.capabilities,
        public_key=Agent.generate_public_key(),
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return ExternalRegisterResponse(
        agent_id=agent.agent_id,
        public_key=agent.public_key,
        registered_at=agent.registered_at,
    )
