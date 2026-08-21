from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.database import PasswordResetRequest, User
from app.schemas.service_desk import PasswordResetCreateRequest, PasswordResetOut

router = APIRouter(prefix="/password-resets", tags=["password-resets"])


@router.get("", response_model=list[PasswordResetOut])
def list_password_resets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(PasswordResetRequest)
        .filter(PasswordResetRequest.user_id == current_user.id)
        .order_by(PasswordResetRequest.created_at.desc())
        .all()
    )


@router.post("", response_model=PasswordResetOut)
def create_password_reset(
    payload: PasswordResetCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reset_request = PasswordResetRequest(
        user_id=current_user.id,
        username=payload.username,
        reason=payload.reason,
        status="queued",
        source="manual",
    )
    db.add(reset_request)
    db.commit()
    db.refresh(reset_request)

    return reset_request


@router.get("/{reset_id}", response_model=PasswordResetOut)
def get_password_reset(
    reset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reset_request = (
        db.query(PasswordResetRequest)
        .filter(PasswordResetRequest.id == reset_id, PasswordResetRequest.user_id == current_user.id)
        .first()
    )
    if not reset_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Password reset request not found."
        )
    return reset_request
