# _*_ coding: utf-8 _*_
from src.database.base import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql.expression import false, func, true

__all__ = [
    "Chat",
    "ChatMessage",
    "MessageRating",
]


class Chat(Base):
    __tablename__ = "CHATS"

    chat_id = Column('CHAT_ID', String(50), primary_key=True)
    chat_title = Column('CHAT_TITLE', String(100), nullable=False)
    user_id = Column('USER_ID', String(50), nullable=False)
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    last_message_at = Column('LAST_MESSAGE_AT', DateTime, nullable=True)
    is_active = Column('IS_ACTIVE', Boolean, nullable=False, server_default=true())
    reviewer_count = Column('REVIEWER_COUNT', Integer, nullable=True, default=0, server_default='0')


class ChatMessage(Base):
    __tablename__ = "CHAT_MESSAGES"

    message_id = Column('MESSAGE_ID', String(50), primary_key=True)
    chat_id = Column('CHAT_ID', String(50), ForeignKey('CHATS.CHAT_ID'), nullable=False)
    user_id = Column('USER_ID', String(50), nullable=False)
    message = Column('MESSAGE', Text, nullable=False)
    message_type = Column('MESSAGE_TYPE', String(20), nullable=False)  # text, image, file, assistant, user, cancelled
    status = Column('STATUS', String(20), nullable=True)  # generating, completed, cancelled, error
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=false())
    is_cancelled = Column('IS_CANCELLED', Boolean, nullable=False, server_default=false())  # 취소된 메시지 표시
    
    # PLC 연결 (PLC 테이블의 ID 참조)
    plc_id = Column('PLC_ID', String(50), ForeignKey('PLC.ID'), nullable=True, index=True)
    
    # External API 노드 처리 결과 저장용 (JSON)
    external_api_nodes = Column('EXTERNAL_API_NODES', JSON, nullable=True)


class MessageRating(Base):
    """메시지 평가 테이블 - AI 답변에 대한 사용자 평가"""
    __tablename__ = "MESSAGE_RATINGS"

    rating_id = Column('RATING_ID', String(50), primary_key=True)
    message_id = Column('MESSAGE_ID', String(50), ForeignKey('CHAT_MESSAGES.MESSAGE_ID'), nullable=False, unique=True)
    user_id = Column('USER_ID', String(50), nullable=False)
    rating_score = Column('RATING_SCORE', Integer, nullable=False)  # 1-5점
    rating_comment = Column('RATING_COMMENT', Text, nullable=True)  # 선택적 코멘트 (향후 확장)
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    updated_at = Column('UPDATED_AT', DateTime, nullable=True, onupdate=func.now())  # 평가 수정 시간
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=false()) 