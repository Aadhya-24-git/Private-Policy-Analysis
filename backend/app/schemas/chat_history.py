import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ChatHistoryBase(BaseModel):
    question: str = Field(min_length=1, description="User prompt or question about document")
    answer: str = Field(min_length=1, description="AI or system auditor response")


class ChatHistoryCreate(ChatHistoryBase):
    document_id: uuid.UUID = Field(description="Associated document UUID")


class ChatHistoryResponse(ChatHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    chat_id: uuid.UUID
    document_id: uuid.UUID
    created_at: datetime
