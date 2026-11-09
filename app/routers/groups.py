
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.membership import Membership
from app.models.user import User
from app.schemas.group import ( GroupCreate, GroupResponse, GroupJoinResponse, GroupMemberResponse, )
from sqlalchemy import select, func, delete
from app.models.message import Message

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
    group_name = group_data.name.strip()

    if not group_name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le nom du groupe ne peut pas être vide.",
        )

    existing_group = db.scalar(
        select(Group).where(func.lower(Group.name) == group_name.lower())
    )

    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce nom de groupe est déjà utilisé.",
        )

    new_group = Group(
        name=group_name,
        description=group_data.description,
        created_by=current_user.id,
    )

    try:
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

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce nom de groupe est déjà utilisé.",
        )

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

@router.delete("/{group_id}")
def delete_group(
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

    if group.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le créateur peut supprimer ce groupe.",
        )

    db.execute(
        delete(Message).where(Message.group_id == group_id)
    )

    db.execute(
        delete(Membership).where(Membership.group_id == group_id)
    )

    db.delete(group)
    db.commit()

    return {
        "message": "Le groupe a été supprimé avec succès."
    }


@router.post("/{group_id}/leave")
def leave_group(
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

    if group.created_by == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le créateur ne peut pas quitter son groupe. Il doit le supprimer.",
        )

    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.group_id == group_id,
        )
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tu n'es pas membre de ce groupe.",
        )

    db.delete(membership)
    db.commit()

    return {
        "message": "Tu as quitté le groupe avec succès."
    }


@router.get(
    "/{group_id}/members",
    response_model=list[GroupMemberResponse],
)
def get_group_members(
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

    current_membership = db.scalar(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.group_id == group_id,
        )
    )

    if not current_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu dois être membre de ce groupe pour voir ses membres.",
        )

    statement = (
        select(User.username, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.group_id == group_id)
        .order_by(User.username)
    )

    members = db.execute(statement).all()

    return [
        {
            "username": member.username,
            "role": member.role,
        }
        for member in members
    ]
