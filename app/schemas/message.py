from datetime import datetime
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: int
    content: str | None
    image_path: str | None
    message_type: str
    user_id: int
    username: str
    group_id: int
    created_at: datetime

    model_config = {"from_attributes": True}