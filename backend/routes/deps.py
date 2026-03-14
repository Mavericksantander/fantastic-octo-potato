import os
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Agent

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

RATE_LIMIT = int(os.getenv("AVOS_RATE_LIMIT", "120"))
RATE_WINDOW_SECONDS = int(os.getenv("AVOS_RATE_WINDOW", "60"))

def _new_bucket():
    now = datetime.utcnow()
    return {"count": 0, "reset": now + timedelta(seconds=RATE_WINDOW_SECONDS)}

_rate_limit_store = defaultdict(_new_bucket)


def _enforce_rate_limit(api_key: str):
    entry = _rate_limit_store[api_key]
    now = datetime.utcnow()
    if now >= entry["reset"]:
        entry["count"] = 0
        entry["reset"] = now + timedelta(seconds=RATE_WINDOW_SECONDS)
    entry["count"] += 1
    if entry["count"] > RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this API key",
        )


def get_current_agent(
    api_key: str = Security(api_key_header), db: Session = Depends(get_db)
) -> Agent:
    agent = db.query(Agent).filter(Agent.public_key == api_key).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    _enforce_rate_limit(api_key)
    return agent


def verify_owner(agent_id: str, current_agent: Agent = Depends(get_current_agent)) -> Agent:
    if agent_id != current_agent.agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent mismatch")
    return current_agent
