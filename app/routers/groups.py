from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.membership import Membership
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse
from app.schemas.group import GroupJoinResponse

router = APIRouter(prefix="/groups", tags=["Groupes"])


@router.post(
    "/",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    group_data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_group = Group(
        name=group_data.name,
        description=group_data.description,
        created_by=current_user.id,
    )

    db.add(new_group)
    db.flush()

    membership = Membership(
        user_id=current_user.id,
        group_id=new_group.id,
        role="admin",
    )

    db.add(membership)
    db.commit()
    db.refresh(new_group)

    return new_group


@router.get("/", response_model=list[GroupResponse])
def get_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Group)
        .join(Membership, Membership.group_id == Group.id)
        .where(Membership.user_id == current_user.id)
        .order_by(Group.created_at.desc())
    )

    return db.scalars(statement).all()

@router.post(
    "/{group_id}/join",
    response_model=GroupJoinResponse,
)
def join_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.get(Group, group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Groupe introuvable.",
        )

    existing_membership = db.scalar(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.group_id == group_id,
        )
    )

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tu es déjà membre de ce groupe.",
        )

    membership = Membership(
        user_id=current_user.id,
        group_id=group_id,
        role="member",
    )

    db.add(membership)
    db.commit()

    return {
        "message": "Tu as rejoint le groupe avec succès.",
        "group_id": group_id,
    }