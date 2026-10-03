import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import ChatHistoryCreate


class ChatHistoryService:
    @staticmethod
    def create(db: Session, chat_in: ChatHistoryCreate) -> ChatHistory:
        db_chat = ChatHistory(
            document_id=chat_in.document_id,
            question=chat_in.question,
            answer=chat_in.answer,
        )
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        return db_chat

    @staticmethod
    def get(db: Session, chat_id: uuid.UUID) -> Optional[ChatHistory]:
        return db.get(ChatHistory, chat_id)

    @staticmethod
    def list_by_document(
        db: Session,
        document_id: uuid.UUID,
        limit: int = 50,
    ) -> List[ChatHistory]:
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.document_id == document_id)
            .order_by(ChatHistory.created_at.asc())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())
