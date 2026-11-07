from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from pathlib import Path
from uuid import uuid4

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import Group
from app.models.membership import Membership
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse


router = APIRouter(prefix="/groups", tags=["Messages"])


def verify_group_membership(
    group_id: int,
    user_id: int,
    db: Session,
):
    membership = db.scalar(
        select(Membership).where(
            Membership.group_id == group_id,
            Membership.user_id == user_id,
        )
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu n'es pas membre de ce groupe.",
        )


def serialize_message(message: Message, username: str):
    return {
        "id": message.id,
        "content": message.content,
        "image_path": message.image_path,
        "message_type": message.message_type,
        "user_id": message.user_id,
        "username": username,
        "group_id": message.group_id,
        "created_at": message.created_at,
    }


@router.post(
    "/{group_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    group_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.get(Group, group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Groupe introuvable.",
        )

    verify_group_membership(group_id, current_user.id, db)

    new_message = Message(
        content=message_data.content,
        message_type="text",
        user_id=current_user.id,
        group_id=group_id,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return serialize_message(new_message, current_user.username)


@router.get(
    "/{group_id}/messages",
    response_model=list[MessageResponse],
)
def get_group_messages(
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

    verify_group_membership(group_id, current_user.id, db)

    statement = (
        select(Message, User.username)
        .join(User, Message.user_id == User.id)
        .where(Message.group_id == group_id)
        .order_by(Message.created_at.asc())
    )

    results = db.execute(statement).all()

    return [
        serialize_message(message, username)
        for message, username in results
    ]


UPLOAD_DIR = Path("app/static/uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo


@router.post(
    "/{group_id}/images",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_image(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = db.get(Group, group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Groupe introuvable.",
        )

    verify_group_membership(group_id, current_user.id, db)

    image_data = await file.read(MAX_FILE_SIZE + 1)

    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="L'image ne doit pas dépasser 5 Mo.",
        )

    if image_data.startswith(b"\xff\xd8\xff"):
        extension = ".jpg"
    elif image_data.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = ".png"
    elif (
        image_data[:4] == b"RIFF"
        and image_data[8:12] == b"WEBP"
    ):
        extension = ".webp"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format invalide. Utilise JPG, PNG ou WEBP.",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename

    file_path.write_bytes(image_data)

    new_message = Message(
        content=None,
        image_path=f"/static/uploads/{filename}",
        message_type="image",
        user_id=current_user.id,
        group_id=group_id,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return serialize_message(new_message, current_user.username)