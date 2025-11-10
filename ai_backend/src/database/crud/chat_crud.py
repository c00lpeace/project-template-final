# _*_ coding: utf-8 _*_
"""Chat CRUD operations with database."""
import logging
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.chat_models import Chat, ChatMessage
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class ChatCRUD:
    """Chat 관련 CRUD 작업을 처리하는 클래스 - DB 기반"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_chat(self, chat_id: str, chat_title: str, user_id: str) -> Chat:
        """채팅 생성"""
        try:
            chat = Chat(
                chat_id=chat_id,
                chat_title=chat_title,
                user_id=user_id,
                create_dt=datetime.now(ZoneInfo("Asia/Seoul")),
                is_active=True  # 활성 상태로 생성
            )
            self.session.add(chat)
            self.session.commit()
            self.session.refresh(chat)
            return chat
        except Exception as e:
            logger.error(f"Database error creating chat: {str(e)}")
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def create_message(
        self, 
        message_id: str, 
        chat_id: str, 
        user_id: str, 
        message: str, 
        message_type: str = "text",
        status: str = None,
        is_cancelled: bool = False,
        plc_id: str = None
    ) -> ChatMessage:
        """메시지 생성"""
        try:
            chat_message = ChatMessage(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                message_type=message_type,
                status=status,
                is_cancelled=is_cancelled,
                plc_id=plc_id,
                create_dt=datetime.now(ZoneInfo("Asia/Seoul"))
            )
            self.session.add(chat_message)
            self.session.commit()
            self.session.refresh(chat_message)
            
            # 채팅의 마지막 메시지 시간 업데이트
            self.update_chat_last_message(chat_id)
            
            return chat_message
        except Exception as e:
            logger.error(f"Database error creating message: {str(e)}")
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_messages(self, chat_id: str, limit: int = 50) -> List[ChatMessage]:
        """특정 채팅의 메시지 조회"""
        try:
            return self.session.query(ChatMessage)\
                .filter(ChatMessage.chat_id == chat_id)\
                .filter(ChatMessage.is_deleted == False)\
                .order_by(ChatMessage.create_dt)\
                .limit(limit)\
                .all()
        except Exception as e:
            logger.error("Database error getting messages: " + str(e))
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """채팅 조회"""
        try:
            return self.session.query(Chat).filter(Chat.chat_id == chat_id).first()
        except Exception as e:
            logger.error(f"Database error getting chat: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_chat_title(self, chat_id: str, new_title: str, user_id: str) -> bool:
        """채팅방 이름 변경"""
        try:
            chat = self.session.query(Chat).filter(
                Chat.chat_id == chat_id,
                Chat.user_id == user_id,
                Chat.is_active == True
            ).first()
            
            if not chat:
                return False
            
            chat.chat_title = new_title
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Database error updating chat title: {str(e)}")
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_chat_or_create(self, chat_id: str, user_id: str = "user") -> Chat:
        """채팅이 없으면 생성하고 반환"""
        try:
            chat = self.get_chat(chat_id)
            if not chat:
                chat = self.create_chat(
                    chat_id=chat_id,
                    chat_title=f"Chat {chat_id}",
                    user_id=user_id
                )
            return chat
        except Exception as e:
            logger.error(f"Database error in get_chat_or_create: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def save_user_message(self, message_id: str, chat_id: str, user_id: str, message: str, plc_id: str = None) -> ChatMessage:
        """사용자 메시지 저장"""
        try:
            return self.create_message(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                message_type="user",
                status="completed",
                plc_id=plc_id
            )
        except Exception as e:
            logger.error(f"Database error saving user message: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def save_ai_message(self, message_id: str, chat_id: str, user_id: str, message: str, status: str = "completed", plc_id: str = None) -> ChatMessage:
        """AI 메시지 저장"""
        try:
            return self.create_message(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                message_type="assistant",
                status=status,
                plc_id=plc_id
            )
        except Exception as e:
            logger.error(f"Database error saving AI message: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_messages_from_db(self, chat_id: str) -> List[dict]:
        """데이터베이스에서 메시지 조회하여 딕셔너리로 변환"""
        try:
            messages = self.get_messages(chat_id)
            
            # ChatMessage 객체를 딕셔너리로 변환
            history = []
            for msg in messages:
                role = "user" if msg.message_type == "user" else "assistant"
                if msg.is_cancelled:
                    role = "system"
                
                history.append({
                    "role": role,
                    "content": msg.message,
                    "timestamp": msg.create_dt.isoformat(),
                    "cancelled": msg.is_cancelled,
                    "message_id": msg.message_id
                })
            
            # 시간순으로 정렬 (오래된 것부터)
            history.sort(key=lambda x: x["timestamp"])
            return history
        except Exception as e:
            logger.error(f"Database error getting messages: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def clear_conversation(self, chat_id: str):
        """대화 기록 초기화 (DB에서 메시지 삭제)"""
        try:
            # 채팅의 모든 메시지를 삭제 상태로 변경
            messages = self.get_messages(chat_id)
            for msg in messages:
                msg.is_deleted = True
            self.session.commit()
        except Exception as e:
            logger.error(f"Database error clearing conversation: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    
    def update_message_to_error(self, message_id: str, error_message):
        """메시지를 에러 상태로 업데이트"""
        try:
            self.update_message_status(message_id, "error")
            # 에러 메시지를 안전하게 문자열로 변환
            safe_error_msg = self._safe_error_message(error_message)
            # 에러 메시지로 업데이트
            message = self.session.query(ChatMessage).filter(ChatMessage.message_id == message_id).first()
            if message:
                message.message = f"❌ 오류가 발생했습니다: {safe_error_msg}"
                self.session.commit()
        except Exception as e:
            logger.error(f"Database error updating message to error: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def _safe_error_message(self, error) -> str:
        """에러 메시지를 안전하게 문자열로 변환"""
        try:
            # AIMessage 객체인지 확인
            if hasattr(error, 'content') and hasattr(error, 'type'):
                return f"AI Message Error: {error.content}"
            # 일반적인 예외 객체
            elif hasattr(error, 'args') and error.args:
                return str(error.args[0]) if len(error.args) == 1 else str(error.args)
            # 기타 객체
            else:
                return str(error)
        except Exception:
            # 모든 변환에 실패한 경우
            return "Unknown error occurred"
    
    def _safe_json_serialize(self, data):
        """데이터를 안전하게 JSON 직렬화 가능한 형태로 변환"""
        import json
        
        def convert_to_serializable(obj):
            if hasattr(obj, 'content') and hasattr(obj, 'type'):
                # AIMessage 객체인 경우
                return {
                    'type': getattr(obj, 'type', 'unknown'),
                    'content': getattr(obj, 'content', ''),
                    'additional_kwargs': getattr(obj, 'additional_kwargs', {})
                }
            elif hasattr(obj, '__dict__'):
                # 객체인 경우 딕셔너리로 변환
                return {k: convert_to_serializable(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        try:
            # 먼저 변환 시도
            serializable_data = convert_to_serializable(data)
            # JSON 직렬화 테스트
            json.dumps(serializable_data)
            return serializable_data
        except Exception as e:
            logger.warning(f"Failed to serialize external_api_nodes: {e}")
            # 실패한 경우 기본값 반환
            return {"error": "Failed to serialize node data", "original_type": str(type(data))}
    
    def get_active_generating_chats(self) -> List[dict]:
        """현재 생성 중인 채팅 목록 반환"""
        try:
            # status가 'generating'인 메시지가 있는 채팅들을 직접 조회
            active_chats = []
            # generating 상태인 메시지들을 조회
            generating_messages = self.session.query(ChatMessage)\
                .filter(ChatMessage.status == "generating")\
                .filter(ChatMessage.is_deleted == False)\
                .all()
            
            # 채팅 ID별로 그룹화
            chat_ids = set(msg.chat_id for msg in generating_messages)
            for chat_id in chat_ids:
                chat = self.get_chat(chat_id)
                if chat:
                    active_chats.append({
                        "chat_id": chat_id,
                        "chat_title": chat.chat_title,
                        "user_id": chat.user_id,
                        "created_at": chat.create_dt.isoformat()
                    })
            
            return active_chats
        except Exception as e:
            logger.error(f"Database error getting active generating chats: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def save_user_message_simple(self, message_id: str, chat_id: str, user_id: str, message: str, plc_id: str = None):
        """사용자 메시지 저장"""
        try:
            self.create_message(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                message_type="user",
                status="completed",
                plc_id=plc_id
            )
        except Exception as e:
            logger.error(f"Database error saving user message: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def save_ai_message_generating(self, message_id: str, chat_id: str, user_id: str, plc_id: str = None):
        """AI 메시지를 generating 상태로 저장"""
        try:
            self.create_message(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                message="",  # 빈 메시지로 시작
                message_type="assistant",
                status="generating",
                plc_id=plc_id
            )
        except Exception as e:
            logger.error(f"Database error saving AI message generating: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_ai_message_completed(self, message_id: str, content: str, external_api_nodes: dict = None):
        """AI 메시지를 완료 상태로 업데이트"""
        try:
            self.update_message_status(message_id, "completed")
            # 메시지 내용도 업데이트
            message = self.session.query(ChatMessage).filter(ChatMessage.message_id == message_id).first()
            if message:
                message.message = content
                # External API 노드 데이터가 있으면 안전하게 저장
                if external_api_nodes:
                    safe_nodes = self._safe_json_serialize(external_api_nodes)
                    message.external_api_nodes = safe_nodes
                    
                    # reviewer_type이 있는지 체크하고 증가
                    self._check_and_increment_reviewer_count(external_api_nodes, message.chat_id)
                
                self.session.commit()
        except Exception as e:
            logger.error(f"Database error updating AI message completed: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_user_chats(self, user_id: str) -> List[Chat]:
        """사용자의 채팅 목록 조회"""
        try:
            return self.session.query(Chat)\
                .filter(Chat.user_id == user_id)\
                .filter(Chat.is_active == True)\
                .order_by(desc(Chat.create_dt))\
                .all()
        except Exception as e:
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_chat_last_message(self, chat_id: str):
        """채팅의 마지막 메시지 시간 업데이트"""
        try:
            chat = self.get_chat(chat_id)
            if chat:
                chat.last_message_at = datetime.now(ZoneInfo("Asia/Seoul"))
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_message_status(self, message_id: str, status: str, is_cancelled: bool = False):
        """메시지 상태 업데이트"""
        try:
            message = self.session.query(ChatMessage).filter(ChatMessage.message_id == message_id).first()
            if message:
                message.status = status
                message.is_cancelled = is_cancelled
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def delete_message(self, message_id: str) -> bool:
        """메시지 삭제 (소프트 삭제)"""
        try:
            message = self.session.query(ChatMessage).filter(ChatMessage.message_id == message_id).first()
            if message:
                message.is_deleted = True
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def delete_chat(self, chat_id: str) -> bool:
        """채팅 삭제 (소프트 삭제)"""
        try:
            chat = self.session.query(Chat).filter(Chat.chat_id == chat_id).first()
            if chat:
                chat.is_active = False
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def increment_reviewer_count(self, chat_id: str) -> bool:
        """리뷰어 카운트 증가 (0 -> 1, 1 -> 2)"""
        try:
            chat = self.session.query(Chat).filter(Chat.chat_id == chat_id).first()
            if chat:
                # 현재 reviewer_count 값에 따라 증가
                if chat.reviewer_count is None or chat.reviewer_count == 0:
                    chat.reviewer_count = 1
                else:
                    chat.reviewer_count = 2
                
                self.session.commit()
                logger.debug(f"Reviewer count incremented for chat {chat_id}: {chat.reviewer_count}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Database error incrementing reviewer count: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_reviewer_count(self, chat_id: str) -> int:
        """채팅의 reviewer_count 조회"""
        try:
            chat = self.session.query(Chat).filter(Chat.chat_id == chat_id).first()
            if chat:
                return chat.reviewer_count or 0  # None인 경우 0 반환
            return 0
        except Exception as e:
            logger.error(f"Database error getting reviewer count: {str(e)}")
            return 0  # 오류 시 기본값 0 반환
    
    def reset_reviewer_count(self, chat_id: str) -> bool:
        """리뷰어 카운트를 0으로 초기화"""
        try:
            chat = self.session.query(Chat).filter(Chat.chat_id == chat_id).first()
            if chat:
                chat.reviewer_count = 0
                self.session.commit()
                logger.debug(f"Reviewer count reset to 0 for chat {chat_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Database error resetting reviewer count: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def _check_and_increment_reviewer_count(self, external_api_nodes: dict, chat_id: str):
        """external_api_nodes에서 agent__reviewer가 있는지 체크하고 reviewer_count 증가 또는 초기화"""
        try:
            # external_api_nodes에서 agent__reviewer가 있는지 재귀적으로 검색
            if self._has_reviewer_type(external_api_nodes):
                logger.info(f"Found agent__reviewer in external_api_nodes for chat {chat_id}, incrementing reviewer_count")
                self.increment_reviewer_count(chat_id)
            else:
                # agent__reviewer가 없으면 카운트를 0으로 초기화
                logger.info(f"No agent__reviewer found in external_api_nodes for chat {chat_id}, resetting reviewer_count to 0")
                self.reset_reviewer_count(chat_id)
        except Exception as e:
            logger.warning(f"Error checking agent__reviewer in external_api_nodes: {str(e)}")
            # agent__reviewer 체크 실패는 전체 프로세스를 중단시키지 않음
    
    def _has_reviewer_type(self, data, visited=None) -> bool:
        """데이터 구조에서 'type': 'agent__reviewer'이 있는지 재귀적으로 검색"""
        if visited is None:
            visited = set()
        
        # 순환 참조 방지
        if id(data) in visited:
            return False
        visited.add(id(data))
        
        try:
            if isinstance(data, dict):
                # 딕셔너리에서 직접 체크
                if data.get('node_type') == 'agent__reviewer':
                    return True
                # 중첩된 딕셔너리들도 재귀적으로 검색
                for value in data.values():
                    if self._has_reviewer_type(value, visited):
                        return True
            elif isinstance(data, (list, tuple)):
                # 리스트/튜플의 각 요소를 재귀적으로 검색
                for item in data:
                    if self._has_reviewer_type(item, visited):
                        return True
        except Exception as e:
            logger.debug(f"Error in _has_agent__reviewer_type: {str(e)}")
        
        return False