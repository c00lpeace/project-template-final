# _*_ coding: utf-8 _*_
"""LLM Chat Service for handling AI conversations."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import tiktoken
from openai import AsyncOpenAI
from sqlalchemy.orm import Session
from src.api.services.llm_provider_factory import BaseLLMProvider, LLMProviderFactory
from src.database.base import Database
from src.database.crud.chat_crud import ChatCRUD
from src.database.crud.user_crud import UserCRUD
from src.database.models.chat_models import ChatMessage
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.uuid_gen import gen

logger = logging.getLogger(__name__)


class LLMChatService:
    """LLM 채팅 서비스를 관리하는 클래스"""
    
    def __init__(self, db: Session = None, redis_client=None):
        # DB 필수 검사
        if db is None:
            raise HandledException(ResponseCode.DATABASE_CONNECTION_ERROR, msg="Database session is required")
        
        # LLM 제공자 팩토리를 사용하여 제공자 생성
        try:
            self.llm_provider = LLMProviderFactory.create_provider()
            logger.info(f"LLM provider initialized: {type(self.llm_provider).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, e=e)
        
        self.db = db  # 이제 Session 객체
        self.redis_client = redis_client
        self.chat_crud = ChatCRUD(db)  # Repository 인스턴스 생성
        self.user_crud = UserCRUD(db)  # User Repository 인스턴스 생성
        
        # LLM 제공자 재생성 (chat_crud, user_crud 전달)
        try:
            self.llm_provider = LLMProviderFactory.create_provider(chat_crud=self.chat_crud, user_crud=self.user_crud)
            logger.info(f"LLM provider re-initialized with chat_crud, user_crud: {type(self.llm_provider).__name__}")
        except Exception as e:
            logger.error(f"Failed to re-initialize LLM provider: {e}")
            # 기존 provider 사용 (ExternalAPIProvider가 아닌 경우)
        
        # 취소 상태 관리
        self.is_cancelled = {}
        
        # 레디스 사용 여부 결정 (로컬: DB만, 운영: 레디스+DB)
        self.use_redis = self._should_use_redis()
        logger.info(f"Cache mode: {'Redis + DB' if self.use_redis else 'DB only'}")
        
        # 토큰 관리 설정
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.llm_provider.model)
            self.max_tokens = 4000  # 안전한 토큰 제한
            self.max_history_tokens = 3000  # 히스토리에 사용할 최대 토큰
        except Exception as e:
            logger.warning(f"Failed to initialize tokenizer: {e}")
            self.tokenizer = None
            self.max_tokens = 4000
            self.max_history_tokens = 3000
    
    def _should_use_redis(self) -> bool:
        """레디스 사용 여부 결정 (로컬: false, 운영: true)"""
        if self.redis_client is None:
            return False
        
        # 레디스 연결 확인
        try:
            if not self.redis_client.ping():
                logger.warning("Redis connection failed, using DB only")
                return False
        except Exception as e:
            logger.warning(f"Redis ping failed: {e}, using DB only")
            return False
        
        # 환경 변수로 강제 설정 가능
        import os
        cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        if not cache_enabled:
            logger.info("CACHE_ENABLED=false, using DB only")
            return False
        
        logger.info("Redis available, using Redis + DB mode")
        return True
    
    def _count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        if self.tokenizer is None:
            # 간단한 추정 (영어 기준 약 4글자 = 1토큰)
            return len(text) // 4
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            return len(text) // 4
    
    def _truncate_messages_by_tokens(self, messages: List[Dict]) -> List[Dict]:
        """토큰 수를 기준으로 메시지 개수를 제한"""
        if not self.tokenizer:
            # 토큰 계산이 불가능한 경우 메시지 개수로 제한
            return messages[-20:]
        
        total_tokens = 0
        truncated_messages = []
        
        # 시스템 프롬프트는 항상 포함
        system_prompt = messages[0] if messages and messages[0].get("role") == "system" else None
        if system_prompt:
            total_tokens += self._count_tokens(system_prompt["content"])
            truncated_messages.append(system_prompt)
        
        # 나머지 메시지를 역순으로 확인 (최신 메시지부터)
        remaining_messages = messages[1:] if system_prompt else messages
        for message in reversed(remaining_messages):
            message_tokens = self._count_tokens(message["content"])
            if total_tokens + message_tokens > self.max_history_tokens:
                break
            total_tokens += message_tokens
            truncated_messages.insert(1 if system_prompt else 0, message)
        
        logger.debug(f"Truncated messages: {len(truncated_messages)} messages, ~{total_tokens} tokens")
        return truncated_messages
    
    def _get_messages_for_openai(self, chat_id: str) -> List[Dict]:
        """메시지를 가져와서 OpenAI 형식으로 변환 (레디스 우선)"""
        messages = []
        
        # 레디스 우선으로 대화 기록 조회
        if self.use_redis:
            try:
                cached_history = self.redis_client.get_chat_messages(chat_id)
                if cached_history:
                    # 캐시된 데이터를 OpenAI 형식으로 변환
                    for msg in cached_history[-20:]:  # 최근 20개로 증가
                        # 취소된 메시지는 제외
                        if msg.get("cancelled", False):
                            continue
                        messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", "")
                        })
                    logger.debug(f"Using cached history for chat {chat_id}: {len(messages)} messages")
                    
                    # 토큰 기반으로 메시지 제한 적용
                    return self._truncate_messages_by_tokens(messages)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        # 레디스에 없거나 실패한 경우 DB에서 조회
        db_messages = self.chat_crud.get_messages(chat_id)
        
        # 최근 20개 메시지만 사용 (토큰 제한 고려)
        for msg in db_messages[-20:]:
            # 취소된 메시지는 제외
            if msg.is_cancelled:
                continue
                
            # 메시지 타입을 role로 변환
            role = msg.message_type
            if msg.message_type == "user":
                role = "user"
            elif msg.message_type == "assistant":
                role = "assistant"
            elif msg.message_type in ["cancelled", "system"]:
                role = "system"
            
            messages.append({
                "role": role,
                "content": msg.message
            })
        
        logger.debug(f"Using DB history for chat {chat_id}: {len(messages)} messages")
        
        # 토큰 기반으로 메시지 제한 적용
        return self._truncate_messages_by_tokens(messages)
    
    def _ensure_chat_exists(self, chat_id: str):
        """채팅이 존재하지 않으면 생성"""
        try:
            # Repository에 세션 전달
            self.chat_crud.get_chat_or_create(chat_id, "user")
        except HandledException:
            raise  # Repository에서 발생한 HandledException 전파
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def send_message_simple(self, chat_id: str, message: str, user_id: str = "user", plc_id: str = None) -> dict:
        """사용자 메시지를 처리하고 LLM 응답을 생성 (REST API용)"""
        try:
            # 비즈니스 로직 검증
            if not message or not message.strip():
                raise HandledException(ResponseCode.CHAT_MESSAGE_INVALID, msg="메시지가 비어있습니다.")
            
            if not chat_id or not chat_id.strip():
                raise HandledException(ResponseCode.CHAT_SESSION_NOT_FOUND, msg="채팅 ID가 유효하지 않습니다.")
            
            # 채팅 존재 확인 및 초기화
            self._ensure_chat_exists(chat_id)
            
            # 사용자 메시지를 DB에 저장
            user_message_id = gen()
            self.chat_crud.save_user_message(user_message_id, chat_id, user_id, message, plc_id=plc_id)
            
            # LLM 응답 생성 (캐시 무효화 없이)
            ai_response = asyncio.run(self._generate_ai_response(chat_id))
            
            # AI 응답을 DB에 저장
            ai_message_id = gen()
            self.chat_crud.save_ai_message(ai_message_id, chat_id, user_id, ai_response, "completed", plc_id=plc_id)
            
            # 메시지 저장 완료 후 캐시 무효화 (한 번만)
            if self.use_redis:
                try:
                    self.redis_client.delete_chat_messages(chat_id)
                    logger.debug(f"Invalidated cache for chat {chat_id} after message completion")
                except Exception as e:
                    logger.warning(f"Redis cache invalidation failed: {e}")
            
            # AI 응답 반환
            return {
                "message_id": ai_message_id,
                "content": ai_response,
                "user_id": user_id,
                "timestamp": self.get_current_timestamp()
            }
            
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            # 에러 발생 시 메시지 상태를 error로 업데이트
            if 'ai_message_id' in locals():
                try:
                    chat_crud = ChatCRUD(self.db)
                    # AIMessage 객체를 안전하게 문자열로 변환
                    error_msg = self._safe_error_message(e)
                    chat_crud.update_message_to_error(ai_message_id, error_msg)
                except HandledException:
                    raise  # Repository에서 발생한 HandledException 전파
                except Exception as db_error:
                    logger.error(f"Failed to update message status to error: {db_error}")
            
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
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
    
    async def _generate_ai_response(self, chat_id: str) -> str:
        """OpenAI API를 사용하여 AI 응답 생성"""
        try:
            # 대화 기록을 가져와서 OpenAI 형식으로 변환
            messages = []
            
            # 레디스 우선으로 대화 기록 조회
            if self.use_redis:
                try:
                    cached_history = self.redis_client.get_chat_messages(chat_id)
                    if cached_history:
                        # 캐시된 데이터 사용
                        for msg in cached_history[-10:]:  # 최근 10개만
                            messages.append({
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", "")
                            })
                    else:
                        # 캐시에 없으면 DB에서 조회
                        messages = self._get_messages_for_openai(chat_id)
                except Exception as e:
                    logger.warning(f"Redis cache read failed: {e}")
                    messages = self._get_messages_for_openai(chat_id)
            else:
                # DB만 사용
                messages = self._get_messages_for_openai(chat_id)
            
            # 시스템 프롬프트 추가
            system_prompt = {
                "role": "system",
                "content": "당신은 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공해주세요."
            }
            messages.insert(0, system_prompt)
            
            logger.info(f"Sending to LLM for chat {chat_id}: {len(messages)} messages total")
            for i, msg in enumerate(messages):
                logger.debug(f"  Message {i}: {msg['role']} - {msg['content'][:100]}...")
            
            # LLM 제공자를 통한 API 호출 (ExternalAPIProvider인 경우 chat_id, user_id 전달)
            # user_id는 _generate_ai_response에서 지원하지 않으므로 기본값 사용
            if hasattr(self.llm_provider, 'create_completion'):
                # create_completion 메서드의 시그니처를 확인하여 chat_id 지원 여부 판단
                import inspect
                sig = inspect.signature(self.llm_provider.create_completion)
                if 'chat_id' in sig.parameters:
                    response = await self.llm_provider.create_completion(messages, chat_id=chat_id)
                else:
                    response = await self.llm_provider.create_completion(messages)
            else:
                response = await self.llm_provider.create_completion(messages)
            
            return response.choices[0].message.content
            
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    
    def get_conversation_history(self, chat_id: str) -> List[Dict]:
        """대화 기록 조회 (레디스 우선, 없으면 DB에서)"""
        try:
            # 비즈니스 로직 검증
            if not chat_id or not chat_id.strip():
                raise HandledException(ResponseCode.CHAT_SESSION_NOT_FOUND, msg="채팅 ID가 유효하지 않습니다.")
            
            if self.use_redis:
                # 레디스에서 먼저 조회
                try:
                    cached_history = self.redis_client.get_chat_messages(chat_id)
                    if cached_history:
                        logger.debug(f"Cache hit for chat {chat_id}")
                        return cached_history
                except Exception as e:
                    logger.warning(f"Redis cache read failed: {e}")
            
            # 레디스에 없거나 실패한 경우 DB에서 조회
            history = self.chat_crud.get_messages_from_db(chat_id)
            
            # 레디스 사용 시 캐시에 저장
            if self.use_redis and history:
                try:
                    self.redis_client.set_chat_messages(chat_id, history, 1800)  # 30분 TTL
                    logger.debug(f"Cached history for chat {chat_id}")
                except Exception as e:
                    logger.warning(f"Redis cache write failed: {e}")
            
            return history
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.CHAT_HISTORY_LOAD_ERROR, e=e)
    
    
    def clear_conversation(self, chat_id: str):
        """대화 기록 초기화 (DB에서 메시지 삭제)"""
        try:
            self.chat_crud.clear_conversation(chat_id)
            
            # 레디스 캐시도 삭제
            if self.use_redis:
                try:
                    # 채팅방 메시지 캐시 삭제
                    self.redis_client.delete_chat_messages(chat_id)
                    
                    # 생성 상태 캐시 삭제
                    generation_key = f"generation:{chat_id}"
                    self.redis_client.redis_client.delete(generation_key)
                    
                    # 취소 상태 캐시 삭제
                    cancel_key = f"cancel:{chat_id}"
                    self.redis_client.redis_client.delete(cancel_key)
                    
                    logger.debug(f"Cleared all cache for chat {chat_id}")
                except Exception as e:
                    logger.warning(f"Redis cache clear failed: {e}")
        except HandledException:
            raise  # Repository에서 발생한 HandledException 전파
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
    
    def get_active_chats(self) -> List[str]:
        """현재 생성 중인 채팅 목록 반환 (DB에서)"""
        try:
            active_chats = self.chat_crud.get_active_generating_chats()
            return [chat["chat_id"] for chat in active_chats]
        except HandledException:
            raise  # Repository에서 발생한 HandledException 전파
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def save_user_message(self, chat_id: str, message: str, user_id: str = "user", plc_id: str = None) -> str:
        """사용자 메시지를 저장하고 메시지 ID 반환"""
        # 세션 존재 확인 및 초기화
        self._ensure_chat_exists(chat_id)
        
        # 사용자 메시지를 DB에 저장
        user_message_id = gen()
        self.chat_crud.save_user_message_simple(user_message_id, chat_id, user_id, message, plc_id=plc_id)
        
        # 스트리밍에서는 캐시 무효화를 하지 않음 (성능 향상)
        # 대화 완료 후에만 캐시를 업데이트
        logger.debug(f"Saved user message for chat {chat_id}")
        
        return user_message_id
    
    async def generate_ai_response_stream(self, chat_id: str, user_id: str = "user", plc_id: str = None):
        """AI 응답을 스트리밍으로 생성"""
        ai_message_id = None
        ai_response_content = ""
        is_cancelled = False
        
        try:
            # 세션 존재 확인 및 초기화
            self._ensure_chat_exists(chat_id)
            
            # 생성 시작 표시 (레디스에 저장)
            if self.use_redis:
                try:
                    generation_key = f"generation:{chat_id}"
                    self.redis_client.redis_client.setex(generation_key, 300, "1")  # 5분 TTL
                except Exception as e:
                    logger.warning(f"Redis generation start failed: {e}")
            
            # 진행 상황 표시
            yield {
                'type': 'progress',
                'step': 'thinking',
                'message': 'AI가 생각하고 있습니다...',
                'timestamp': self.get_current_timestamp()
            }
            
            # 취소 확인
            if self.is_cancelled.get(chat_id, False):
                is_cancelled = True
                yield {
                    'type': 'cancelled',
                    'message': '사용자에 의해 취소되었습니다.',
                    'timestamp': self.get_current_timestamp()
                }
                return
            
            # 대화 기록을 가져와서 OpenAI 형식으로 변환 (레디스 우선)
            messages = self._get_messages_for_openai(chat_id)
            
            # 시스템 프롬프트 추가
            system_prompt = {
                "role": "system",
                "content": "당신은 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공해주세요."
            }
            messages.insert(0, system_prompt)
            
            logger.info(f"Streaming to LLM for chat {chat_id}: {len(messages)} messages total")
            for i, msg in enumerate(messages):
                logger.debug(f"  Stream Message {i}: {msg['role']} - {msg['content'][:100]}...")
            
            # 진행 상황 표시
            yield {
                'type': 'progress',
                'step': 'generating',
                'message': 'AI가 응답을 생성하고 있습니다...',
                'timestamp': self.get_current_timestamp()
            }
            
            # 취소 확인
            if self.is_cancelled.get(chat_id, False):
                is_cancelled = True
                yield {
                    'type': 'cancelled',
                    'message': '사용자에 의해 취소되었습니다.',
                    'timestamp': self.get_current_timestamp()
                }
                return
            
            # LLM 제공자를 통한 스트리밍 API 호출 (ExternalAPIProvider인 경우 chat_id, user_id 전달)
            if hasattr(self.llm_provider, 'create_completion'):
                # create_completion 메서드의 시그니처를 확인하여 chat_id, user_id 지원 여부 판단
                import inspect
                sig = inspect.signature(self.llm_provider.create_completion)
                if 'chat_id' in sig.parameters and 'user_id' in sig.parameters:
                    stream = await self.llm_provider.create_completion(messages, stream=True, chat_id=chat_id, user_id=user_id)
                elif 'chat_id' in sig.parameters:
                    stream = await self.llm_provider.create_completion(messages, stream=True, chat_id=chat_id)
                else:
                    stream = await self.llm_provider.create_completion(messages, stream=True)
            else:
                stream = await self.llm_provider.create_completion(messages, stream=True)
            
            ai_response_content = ""
            ai_message_id = gen()
            
            # AI 응답을 진행중 상태로 DB에 저장
            self.chat_crud.save_ai_message_generating(ai_message_id, chat_id, user_id, plc_id=plc_id)
            
            async for chunk in stream:
                # 취소 확인 (레디스 우선)
                if self.use_redis:
                    try:
                        cancel_key = f"cancel:{chat_id}"
                        if self.redis_client.redis_client.exists(cancel_key):
                            is_cancelled = True
                            logger.info(f"Cancellation detected in stream for session: {chat_id}")
                            yield {
                                'type': 'cancelled',
                                'message': '사용자에 의해 취소되었습니다.',
                                'timestamp': self.get_current_timestamp()
                            }
                            break
                    except Exception as e:
                        logger.warning(f"Redis cancel check failed: {e}")
                
                # 레디스에 없거나 실패한 경우 DB에서 확인
                if not is_cancelled:
                    try:
                        messages = self.chat_crud.get_messages(chat_id)
                        if messages and messages[-1].is_cancelled:
                            is_cancelled = True
                            logger.info(f"Cancellation detected in stream for session: {chat_id}")
                            yield {
                                'type': 'cancelled',
                                'message': '사용자에 의해 취소되었습니다.',
                                'timestamp': self.get_current_timestamp()
                            }
                            break
                    except Exception as e:
                        logger.warning(f"DB cancel check failed: {e}")
                
                # Provider별 스트림 청크 처리
                content = self.llm_provider.process_stream_chunk(chunk)
                if content is not None:
                    ai_response_content += content
                    
                    # 부분 응답 스트림
                    yield {
                        'type': 'ai_response_chunk',
                        'message_id': ai_message_id,
                        'content': content,
                        'user_id': user_id,
                        'timestamp': self.get_current_timestamp()
                    }
            
            # 취소되지 않은 경우에만 완전한 응답 처리
            if not is_cancelled and ai_response_content:
                # External API provider인 경우 노드 데이터 저장
                if hasattr(self.llm_provider, 'get_collected_node_data'):
                    node_data = self.llm_provider.get_collected_node_data()
                    if node_data:
                        # 노드 데이터와 함께 메시지 완료 업데이트
                        self.chat_crud.update_ai_message_completed(ai_message_id, ai_response_content, node_data)
                        # 노드 데이터 초기화
                        self.llm_provider.clear_node_data()
                    else:
                        self.chat_crud.update_ai_message_completed(ai_message_id, ai_response_content)
                else:
                    # 일반 provider인 경우
                    self.chat_crud.update_ai_message_completed(ai_message_id, ai_response_content)
                
                # 스트리밍 완료 후 캐시 무효화
                if self.use_redis:
                    try:
                        self.redis_client.delete_chat_messages(chat_id)
                        logger.debug(f"Invalidated cache for chat {chat_id} after streaming completion")
                    except Exception as e:
                        logger.warning(f"Redis cache invalidation failed: {e}")
                
                # 완료 표시
                yield {
                    'type': 'ai_response_complete',
                    'message_id': ai_message_id,
                    'content': ai_response_content,
                    'user_id': user_id,
                    'timestamp': self.get_current_timestamp()
                }
            else:
                # 취소된 경우 - 메시지 처리
                try:
                    if ai_message_id:
                        self.chat_crud.update_message_to_error(ai_message_id, "⚠️ 응답이 취소되었습니다.")
                    else:
                        # ai_message_id가 없으면 새로 생성
                        ai_message_id = gen()
                        
                        # 채팅방이 존재하는지 확인하고, 없으면 생성
                        chat = self.chat_crud.get_chat(chat_id)
                        if not chat:
                            self.chat_crud.create_chat(
                                chat_id=chat_id,
                                chat_title=f"Chat {chat_id}",
                                user_id=user_id
                            )
                            
                        # 취소 메시지 저장
                        self.chat_crud.create_message(
                            message_id=ai_message_id,
                            chat_id=chat_id,
                            user_id=user_id,
                            message="⚠️ 응답이 취소되었습니다.",
                            message_type="assistant",
                            status="cancelled",
                            is_cancelled=True,
                            plc_id=plc_id
                        )
                            
                except Exception as e:
                    # DB 저장 실패 시에도 메시지 ID 생성
                    if not ai_message_id:
                        ai_message_id = gen()
                
                # DB에 이미 저장되었으므로 메모리 저장 불필요
                
                # 취소 완료 메시지 스트림 전송
                yield {
                    'type': 'cancelled',
                    'message_id': ai_message_id,
                    'content': '⚠️ 응답이 취소되었습니다.',
                    'user_id': user_id,
                    'timestamp': self.get_current_timestamp()
                }
            
        except HandledException as e:
            # HandledException은 스트림으로 전달 (연결 유지)
            if ai_message_id:
                try:
                    self.chat_crud.update_message_status(ai_message_id, "error")
                    # 에러 메시지로 업데이트
                    message = self.db.query(ChatMessage).filter(ChatMessage.message_id == ai_message_id).first()
                    if message:
                        message.message = f"❌ 오류가 발생했습니다: {e.message}"
                        self.db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update message status to error: {db_error}")
            
            # 스트리밍 에러 응답 생성
            from src.types.response.chat_response import StreamErrorResponse
            error_response = StreamErrorResponse(
                code=e.code,
                message=e.message,
                content=f"AI 응답 생성 중 오류가 발생했습니다: {e.message}",
                timestamp=self.get_current_timestamp(),
                chat_id=chat_id
            )
            yield error_response.dict()
        except Exception as e:
            # 에러 발생 시 메시지 상태를 error로 업데이트
            if ai_message_id:
                try:
                    self.chat_crud.update_message_status(ai_message_id, "error")
                    # 에러 메시지로 업데이트
                    message = self.db.query(ChatMessage).filter(ChatMessage.message_id == ai_message_id).first()
                    if message:
                        message.message = f"❌ 오류가 발생했습니다: {str(e)}"
                        self.db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to update message status to error: {db_error}")
            
            
            # 스트리밍 에러 응답 생성
            from src.types.response.chat_response import StreamErrorResponse
            error_response = StreamErrorResponse(
                code=-2,  # UNDEFINED_ERROR
                message="정의되지 않은 오류입니다.",
                content=f"AI 응답 생성 중 예상치 못한 오류가 발생했습니다: {str(e)}",
                timestamp=self.get_current_timestamp(),
                chat_id=chat_id
            )
            yield error_response.dict()
        finally:
            # 생성 완료 - 레디스에서 생성 상태 제거
            if self.use_redis:
                try:
                    generation_key = f"generation:{chat_id}"
                    self.redis_client.redis_client.delete(generation_key)
                except Exception as e:
                    logger.warning(f"Redis generation cleanup failed: {e}")
    
    async def cancel_generation(self, chat_id: str, user_id: str = "user"):
        """현재 생성 중인 AI 응답을 취소"""
        try:
            # 비즈니스 로직 검증
            if not chat_id or not chat_id.strip():
                raise HandledException(ResponseCode.CHAT_SESSION_NOT_FOUND, msg="채팅 ID가 유효하지 않습니다.")
            
            # 세션 존재 확인 및 초기화
            self._ensure_chat_exists(chat_id)
            
            # 레디스에서 생성 상태 확인
            if self.use_redis:
                try:
                    generation_key = f"generation:{chat_id}"
                    if self.redis_client.redis_client.exists(generation_key):
                        # 레디스에서 생성 상태 제거
                        self.redis_client.redis_client.delete(generation_key)
                        
                        # 취소 상태를 레디스에 저장
                        cancel_key = f"cancel:{chat_id}"
                        self.redis_client.redis_client.setex(cancel_key, 60, "1")  # 1분 TTL
                        
                        logger.info(f"Generation cancelled for session: {chat_id}")
                        return True
                except Exception as e:
                    logger.warning(f"Redis cancel check failed: {e}")
            
            # DB에서 현재 생성 중인 메시지가 있는지 확인
            messages = self.chat_crud.get_messages(chat_id)
            
            # 최근 메시지가 generating 상태인지 확인
            if messages and messages[-1].status == "generating":
                # 생성 중인 메시지를 취소 상태로 변경
                messages[-1].status = "cancelled"
                messages[-1].is_cancelled = True
                messages[-1].message = "⚠️ 응답이 취소되었습니다."
                self.db.commit()
                logger.info(f"Generation cancelled for session: {chat_id}")
                return True
            else:
                # 생성이 완료되었거나 시작되지 않은 경우에도 취소 메시지 저장
                await self._save_cancelled_message_standalone(chat_id, user_id)
                logger.info(f"No active generation to cancel for session: {chat_id}, but saved cancelled message")
                return True
                
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.CHAT_GENERATION_CANCEL_ERROR, e=e)
    
    async def _save_cancelled_message_standalone(self, chat_id: str, user_id: str = "user"):
        """독립적으로 취소 메시지를 저장하는 메서드"""
        try:
            # 메시지 ID 생성
            ai_message_id = gen()
            
            # 채팅방이 존재하는지 확인하고, 없으면 생성
            chat = self.chat_crud.get_chat(chat_id)
            if not chat:
                self.chat_crud.create_chat(
                    chat_id=chat_id,
                    chat_title=f"Chat {chat_id}",
                    user_id=user_id
                )
            
            # 취소 메시지 저장
            self.chat_crud.create_message(
                message_id=ai_message_id,
                chat_id=chat_id,
                user_id=user_id,
                message="⚠️ 응답이 취소되었습니다.",
                message_type="assistant",
                status="cancelled",
                is_cancelled=True,
                plc_id=None
            )
            
            # DB에 이미 저장되었으므로 메모리 저장 불필요
            
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def is_generating(self, chat_id: str) -> bool:
        """현재 생성 중인지 확인 (레디스 우선)"""
        # 레디스에서 먼저 확인
        if self.use_redis:
            try:
                # 레디스에서 생성 상태 확인 (간단한 키-값 체크)
                generation_key = f"generation:{chat_id}"
                return self.redis_client.redis_client.exists(generation_key)
            except Exception as e:
                logger.warning(f"Redis generation check failed: {e}")
        
        # 레디스에 없거나 실패한 경우 DB에서 확인
        messages = self.chat_crud.get_messages(chat_id)
        # 최근 메시지가 generating 상태인지 확인
        return messages and messages[-1].status == "generating"
    
    def create_chat(self, chat_title: str, user_id: str) -> str:
        """새로운 채팅 생성"""
        chat_id = gen()
        
        self.chat_crud.create_chat(chat_id, chat_title, user_id)
        
        logger.info(f"Created chat: {chat_id} for user: {user_id}")
        return chat_id
    
    def get_user_chats(self, user_id: str) -> List[Dict]:
        """사용자의 채팅 목록 조회"""
        chats = self.chat_crud.get_user_chats(user_id)
        return [
            {
                "chat_id": chat.chat_id,
                "chat_title": chat.chat_title,
                "user_id": chat.user_id,
                "created_at": chat.create_dt.isoformat(),
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None
            }
            for chat in chats
        ]
    
    def delete_chat(self, chat_id: str) -> bool:
        """채팅 삭제"""
        try:
            # 비즈니스 로직 검증
            if not chat_id or not chat_id.strip():
                raise HandledException(ResponseCode.CHAT_SESSION_NOT_FOUND, msg="채팅 ID가 유효하지 않습니다.")
            
            success = self.chat_crud.delete_chat(chat_id)
            
            # DB 삭제 성공 시 Redis 캐시도 삭제
            if success and self.use_redis:
                try:
                    # 채팅방 관련 모든 캐시 삭제
                    self.redis_client.delete_chat_messages(chat_id)
                    
                    # 생성 상태 캐시 삭제
                    generation_key = f"generation:{chat_id}"
                    self.redis_client.redis_client.delete(generation_key)
                    
                    # 취소 상태 캐시 삭제
                    cancel_key = f"cancel:{chat_id}"
                    self.redis_client.redis_client.delete(cancel_key)
                    
                    logger.debug(f"Cleared all cache for deleted chat {chat_id}")
                except Exception as e:
                    logger.warning(f"Redis cache cleanup failed for chat {chat_id}: {e}")
            
            return success
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.CHAT_DELETE_ERROR, e=e)
    
    def get_chat_info(self, chat_id: str) -> Optional[Dict]:
        """채팅 정보 조회"""
        chat = self.chat_crud.get_chat(chat_id)
        if chat:
            return {
                "chat_id": chat.chat_id,
                "chat_title": chat.chat_title,
                "user_id": chat.user_id,
                "created_at": chat.create_dt.isoformat(),
                "last_message_at": chat.last_message_at.isoformat() if chat.last_message_at else None
            }
        return None
    
    def update_chat_last_message(self, chat_id: str):
        """채팅 마지막 메시지 시간 업데이트"""
        self.chat_crud.update_chat_last_message(chat_id)
    
    async def generate_chat_title(self, message: str) -> str:
        """질문을 기반으로 채팅 제목을 생성합니다."""
        try:
            # LLM 제공자를 사용하여 제목 생성
            response = await self.llm_provider.create_title_completion(message)
            
            title = response.choices[0].message.content.strip()
            
            # 제목이 너무 길면 자르기
            if len(title) > 20:
                title = title[:17] + "..."
            
            # 빈 제목이면 기본값
            if not title:
                title = f"Chat {datetime.now().strftime('%H:%M')}"
            
            return title
            
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            # 실패 시 간단한 제목 생성 (HandledException으로 변환하지 않음 - 제목 생성은 선택적 기능)
            words = message.split()[:3]  # 처음 3개 단어만 사용
            title = " ".join(words)
            if len(title) > 15:
                title = title[:12] + "..."
            return title if title else f"Chat {datetime.now().strftime('%H:%M')}"
    
    def update_chat_title(self, chat_id: str, new_title: str, user_id: str) -> bool:
        """채팅방 이름 변경"""
        try:
            # CRUD를 통해 채팅방 이름 변경
            success = self.chat_crud.update_chat_title(chat_id, new_title, user_id)
            
            if not success:
                raise HandledException(ResponseCode.CHAT_NOT_FOUND, msg="채팅방을 찾을 수 없습니다.")
            
            return True
            
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.CHAT_UPDATE_ERROR, e=e)