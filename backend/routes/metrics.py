from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuthorizationLog

router = APIRouter()


@router.get("/metrics/blocked_actions")
def blocked_actions(db: Session = Depends(get_db)):
    """Expose a simple counter of authorization events that were not allowed."""
    blocked_count = (
        db.query(AuthorizationLog)
        .filter(AuthorizationLog.decision != "allow")
        .count()
    )
    return {"blocked_actions_count": blocked_count}
