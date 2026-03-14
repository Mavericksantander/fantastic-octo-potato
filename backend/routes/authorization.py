import json
from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Agent, AgentTask, AuthorizationLog
from .deps import get_current_agent

router = APIRouter()

BLOCKED_COMMANDS = ["rm -rf", "mkfs", "dd if=", "shutdown", "reboot", ":/", "sudo"]
SPEND_THRESHOLD = float(1000)


class AuthorizationRequest(BaseModel):
    agent_id: str
    action_type: str
    action_payload: Dict[str, Any] = Field(default_factory=dict)


class AuthorizationResponse(BaseModel):
    decision: str
    reason: str


def _evaluate_action(action_type: str, payload: Dict[str, Any]) -> Tuple[str, str]:
    payload = payload or {}
    decision = "allow"
    reason = ""
    if action_type == "execute_shell_command":
        command = str(payload.get("command", "")).lower()
        if any(phrase in command for phrase in BLOCKED_COMMANDS) or "rm -rf" in command:
            return "deny", "Destructive command detected"
        if payload.get("requires_root"):
            return "require_verification", "Root-level command needs extra confirmation"
    if action_type == "modify_file":
        target = payload.get("path", "")
        if target.startswith("/etc") or target.startswith("/usr/bin"):
            return "deny", "Changing critical system files is blocked"
    if action_type == "call_external_api":
        domain = payload.get("domain", "")
        if not domain or domain.endswith(".internal"):
            return "deny", "External API target is not approved"
    if action_type == "spend_money":
        amount = float(payload.get("amount", 0))
        if amount > SPEND_THRESHOLD:
            return "require_verification", "Spending exceeds allowed threshold"
    return decision, reason or "Action classified as safe"


@router.post("/authorize_action", response_model=AuthorizationResponse)
def authorize_action(
    payload: AuthorizationRequest,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent),
):
    if payload.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent mismatch")
    decision, reason = _evaluate_action(payload.action_type, payload.action_payload or {})
    log = AuthorizationLog(
        agent_id=current_agent.agent_id,
        action_type=payload.action_type,
        payload=json.dumps(payload.action_payload or {}),
        decision=decision,
        reason=reason,
        blocked_reason=reason if decision != "allow" else None,
    )
    db.add(log)
    db.commit()
    return AuthorizationResponse(decision=decision, reason=reason)


@router.get("/authorization/logs")
def authorization_logs(limit: int = 20, db: Session = Depends(get_db), current_agent: Agent = Depends(get_current_agent)):
    logs = (
        db.query(AuthorizationLog)
        .filter(AuthorizationLog.agent_id == current_agent.agent_id)
        .order_by(AuthorizationLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "action_type": log.action_type,
            "decision": log.decision,
            "reason": log.reason,
            "timestamp": log.timestamp,
        }
        for log in logs
    ]


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total_agents = db.query(Agent).count()
    now = datetime.utcnow()
    active_threshold = now - timedelta(minutes=5)
    active_agents = (
        db.query(Agent)
        .filter(Agent.last_heartbeat_at != None)
        .filter(Agent.last_heartbeat_at >= active_threshold)
        .all()
    )
    top_agents = (
        db.query(Agent)
        .order_by(Agent.reputation_score.desc())
        .limit(5)
        .all()
    )
    tasks = (
        db.query(AgentTask)
        .order_by(AgentTask.logged_at.desc())
        .limit(15)
        .all()
    )
    denied = (
        db.query(AuthorizationLog)
        .filter(AuthorizationLog.decision != "allow")
        .order_by(AuthorizationLog.timestamp.desc())
        .limit(10)
        .all()
    )
    return {
        "total_agents": total_agents,
        "active_agent_count": len(active_agents),
        "active_agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "last_heartbeat": agent.last_heartbeat_at,
            }
            for agent in active_agents
        ],
        "top_agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "reputation_score": agent.reputation_score,
                "capabilities": agent.capabilities or [],
            }
            for agent in top_agents
        ],
        "recent_tasks": [
            {
                "agent_id": task.agent_id,
                "description": task.task_description,
                "result_status": task.result_status,
                "execution_time": task.execution_time,
                "logged_at": task.logged_at,
            }
            for task in tasks
        ],
        "recent_blocked_actions": [
            {
                "agent_id": log.agent_id,
                "action_type": log.action_type,
                "decision": log.decision,
                "reason": log.reason,
                "blocked_reason": log.blocked_reason,
                "timestamp": log.timestamp,
            }
            for log in denied
        ],
    }
