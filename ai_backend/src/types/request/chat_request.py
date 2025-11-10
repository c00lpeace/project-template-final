# _*_ coding: utf-8 _*_
"""Chat request models."""
from pydantic import BaseModel, Field
from typing import Optional


class UserMessageRequest(BaseModel):
    """사용자 메시지 요청 모델"""
    type: str = Field(default="user_message", description="메시지 타입")
    message: str = Field(..., min_length=1, max_length=4000, description="사용자 메시지")
    user_id: str = Field(default="user", description="사용자 ID")
    plc_id: Optional[str] = Field(default=None, description="PLC ID (PLC 테이블의 ID)")


class ClearConversationRequest(BaseModel):
    """대화 기록 초기화 요청 모델"""
    type: str = Field(default="clear_conversation", description="메시지 타입")


class GetHistoryRequest(BaseModel):
    """대화 기록 조회 요청 모델"""
    type: str = Field(default="get_history", description="메시지 타입")


class CreateChatRequest(BaseModel):
    """채팅 생성 요청 모델"""
    chat_title: str = Field(..., min_length=1, max_length=100, description="채팅 제목")
    user_id: str = Field(..., min_length=1, max_length=50, description="사용자 ID")
