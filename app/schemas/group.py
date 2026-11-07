from datetime import datetime

from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str | None = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupJoinResponse(BaseModel):
    message: str
    group_id: int