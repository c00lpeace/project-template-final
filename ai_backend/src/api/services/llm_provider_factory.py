# _*_ coding: utf-8 _*_
"""LLM Provider Factory for supporting multiple LLM providers."""
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional

import aiohttp
from langserve import RemoteRunnable
from openai import AsyncOpenAI
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class BaseLLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, model, max_tokens=1000, temperature=0.7):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    async def create_completion(self, messages, stream=False):
        """Create completion from LLM provider"""
        raise NotImplementedError("Subclasses must implement create_completion")
    
    async def create_title_completion(self, message):
        """Create title completion from LLM provider"""
        raise NotImplementedError("Subclasses must implement create_title_completion")
    
    def process_stream_chunk(self, chunk):
        """Process streaming chunk and extract content"""
        raise NotImplementedError("Subclasses must implement process_stream_chunk")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, api_key: str, base_url: str, model: str = "gpt-3.5-turbo", max_tokens: int = 1000, temperature: float = 0.7):
        super().__init__(model, max_tokens, temperature)
        
        if not api_key:
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, msg="OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        logger.info("OpenAI provider initialized with model: " + str(model))
    
    async def create_completion(self, messages: list, stream: bool = False):
        """Create completion using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=stream
            )
            return response
        except Exception as e:
            logger.error("OpenAI API error: " + str(e))
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    async def create_title_completion(self, message: str):
        """Create title completion using OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "다음 질문을 기반으로 간단하고 명확한 채팅방 제목을 생성해주세요. 20자 이내로 만들어주세요."
                    },
                    {
                        "role": "user",
                        "content": "질문: " + str(message)
                    }
                ],
                max_tokens=50,
                temperature=self.temperature
            )
            return response
        except Exception as e:
            logger.error("OpenAI title generation error: " + str(e))
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    def process_stream_chunk(self, chunk) -> str:
        """Process OpenAI streaming chunk and extract content"""
        if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
            return chunk.choices[0].delta.content
        return None


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI provider implementation"""
    
    def __init__(self, api_key: str, endpoint: str, deployment_name: str, 
                 api_version: str, max_tokens: int = 1000, temperature: float = 0.7):
        super().__init__(deployment_name, max_tokens, temperature)
        
        if not api_key:
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, msg="Azure OpenAI API key is required")
        if not endpoint:
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, msg="Azure OpenAI endpoint is required")
        if not deployment_name:
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, msg="Azure OpenAI deployment name is required")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=endpoint.rstrip('/') + "/openai/deployments/" + deployment_name,
            default_query={"api-version": api_version}
        )
        logger.info("Azure OpenAI provider initialized with deployment: " + str(deployment_name))
    
    async def create_completion(self, messages: list, stream: bool = False):
        """Create completion using Azure OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,  # deployment name
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=stream
            )
            return response
        except Exception as e:
            logger.error("Azure OpenAI API error: " + str(e))
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    async def create_title_completion(self, message: str):
        """Create title completion using Azure OpenAI API"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,  # deployment name
                messages=[
                    {
                        "role": "system",
                        "content": "다음 질문을 기반으로 간단하고 명확한 채팅방 제목을 생성해주세요. 20자 이내로 만들어주세요."
                    },
                    {
                        "role": "user",
                        "content": "질문: " + str(message)
                    }
                ],
                max_tokens=50,
                temperature=self.temperature
            )
            return response
        except Exception as e:
            logger.error("Azure OpenAI title generation error: " + str(e))
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    def process_stream_chunk(self, chunk) -> str:
        """Process Azure OpenAI streaming chunk and extract content"""
        # Azure OpenAI의 첫 번째 청크는 빈 choices 배열을 가질 수 있음
        if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content is not None:
            return chunk.choices[0].delta.content
        return None


class ExternalAPIProvider(BaseLLMProvider):
    """External API Agent provider implementation using LangServe RemoteRunnable"""
    
    def __init__(self, api_url: str, authorization_header: str, 
                 max_tokens: int = 1000, temperature: float = 0.7, chat_crud=None, user_crud=None):
        super().__init__("external_api", max_tokens, temperature)
        
        if not api_url:
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, msg="External API URL is required")
        if not authorization_header:
            raise HandledException(ResponseCode.LLM_CONFIG_ERROR, msg="Authorization header is required")
        
        self.api_url = api_url.rstrip('/')
        self.authorization_header = authorization_header
        self.node_data = {}  # 노드 데이터를 메모리에 수집
        self.chat_crud = chat_crud  # DB 접근을 위한 ChatCRUD 인스턴스
        self.user_crud = user_crud  # DB 접근을 위한 UserCRUD 인스턴스
        
        # LangServe RemoteRunnable 초기화
        headers = {
            "Authorization": self.authorization_header,
        }
        
        self.agent = RemoteRunnable(
            self.api_url,
            headers=headers
        )
        
        logger.info("External API provider initialized with URL: " + str(self.api_url))
    
    async def create_completion(self, messages: list, stream: bool = False, chat_id: str = None, user_id: str = None):
        """Create completion using External API via LangServe RemoteRunnable"""
        try:
            # OpenAI 형식의 messages를 LangServe 형식으로 변환
            langserve_messages = []
            for msg in messages:
                if msg["role"] == "human" or msg["role"] == "user":
                    langserve_messages.append({
                        "content": msg["content"],
                        "type": "human"
                    })
                elif msg["role"] == "assistant":
                    langserve_messages.append({
                        "content": msg["content"],
                        "type": "ai"
                    })
                elif msg["role"] == "system":
                    # 시스템 메시지는 첫 번째 human 메시지에 포함
                    if langserve_messages and langserve_messages[0]["type"] == "human":
                        langserve_messages[0]["content"] = msg["content"] + "\n\n" + langserve_messages[0]["content"]
                    else:
                        langserve_messages.insert(0, {
                            "content": msg["content"],
                            "type": "human"
                        })
            
            # additional_kwargs에 기본값들과 reviewer_count 추가
            additional_kwargs = {
                "auth_level": "admin"  # 기본 auth_level
            }
            
            if chat_id and self.chat_crud:
                try:
                    reviewer_count = self.chat_crud.get_reviewer_count(chat_id)
                    additional_kwargs["reviewer_count"] = reviewer_count
                    logger.debug(f"Added reviewer_count to additional_kwargs: {reviewer_count}")
                except Exception as e:
                    logger.warning(f"Failed to get reviewer_count for chat {chat_id}: {e}")
                    additional_kwargs["reviewer_count"] = 0  # 기본값
            
            # user_id로 user 정보 조회하여 site_list 추가
            if user_id and self.user_crud:
                try:
                    user = self.user_crud.get_user(user_id)
                    if user and user.site_list:
                        additional_kwargs["site_list"] = user.site_list
                        logger.debug(f"Added site_list to additional_kwargs for user {user_id}: {user.site_list}")
                except Exception as e:
                    logger.warning(f"Failed to get site_list for user {user_id}: {e}")
            
            request_body = {
                "messages": langserve_messages,
                "additional_kwargs": additional_kwargs
            }
            
            if stream:
                # 스트리밍의 경우 async generator를 직접 반환
                return self._create_streaming_completion(request_body)
            else:
                return await self._create_non_streaming_completion(request_body)
                
        except Exception as e:
            logger.error("External API error: " + str(e))
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    async def _create_streaming_completion(self, request_body: dict):
        """Create streaming completion using LangServe RemoteRunnable"""
        try:
            # LangServe RemoteRunnable의 stream 메서드 사용
            async for chunk in self.agent.astream(request_body):
                logger.debug(f"Received chunk: {chunk}")
                
                # LangServe 스타일의 청크 처리
                content = self._extract_content_from_chunk(chunk)
                if content is not None:
                    yield self._create_chunk_object({'content': content})
                    
        except Exception as e:
            logger.error(f"LangServe streaming error: {e}")
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    
    def _extract_content_from_chunk(self, chunk_data: dict):
        """청크 데이터에서 스트리밍할 컨텐츠 추출"""
        # LangServe 스타일의 청크 처리
        if chunk_data.get("final_result"):
            return chunk_data["final_result"]
        elif chunk_data.get("llm"):
            # LLM 중간 토큰은 스트리밍하지 않음
            logger.debug(f"LLM intermediate token: {chunk_data}")
            return None
        elif chunk_data.get("updates"):
            # 노드 업데이트는 스트리밍하지 않지만 데이터 저장
            logger.debug(f"Node updates: {chunk_data}")
            self._store_node_data(chunk_data)
            return None
        elif chunk_data.get("progress"):
            # 진행상황은 스트리밍하지 않음
            logger.debug(f"Progress: {chunk_data}")
            return None
        elif chunk_data.get("error"):
            # 에러 메시지
            error_msg = chunk_data.get('error', 'Unknown error')
            logger.error(f"External API error: {error_msg}")
            return None
        
        return None
    
    
    def _store_node_data(self, chunk_data: dict):
        """노드 결과 데이터를 메모리에 수집 (LangServe 스타일)"""
        # 노드 기본 정보 추출
        node_name = chunk_data.get('node_name', 'unknown')
        node_type = chunk_data.get('node_type', 'unknown')
        updates = chunk_data.get('updates', {})
        
        # 노드 데이터 구조화
        node_data = {
            'node_name': node_name,
            'node_type': node_type,
            'updates': updates
        }
        
        # 추가 필드들도 포함
        for key, value in chunk_data.items():
            if key not in ['node_name', 'node_type', 'updates']:
                node_data[key] = value
        
        # 노드 데이터를 메모리에 저장
        self.node_data[node_name] = node_data
        logger.debug(f"Node '{node_name}' ({node_type}) data collected: {node_data}")
    
    def get_collected_node_data(self):
        """수집된 노드 데이터 반환"""
        return self.node_data.copy()
    
    def clear_node_data(self):
        """노드 데이터 초기화"""
        self.node_data.clear()
    
    
    async def _create_non_streaming_completion(self, request_body: dict):
        """Create non-streaming completion using LangServe RemoteRunnable"""
        try:
            # LangServe RemoteRunnable의 invoke 메서드 사용
            response_data = await self.agent.ainvoke(request_body)
            return self._create_completion_object(response_data)
        except Exception as e:
            logger.error(f"LangServe non-streaming error: {e}")
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    def _create_chunk_object(self, chunk_data: dict):
        """External API 응답을 OpenAI 스타일 청크 객체로 변환"""
        class ChunkObject:
            def __init__(self, content):
                self.choices = [type('Choice', (), {
                    'delta': type('Delta', (), {'content': content})()
                })()]
        
        # External API 응답에서 content 추출 (실제 응답 구조에 따라 조정 필요)
        content = chunk_data.get('content', '') or chunk_data.get('text', '')
        return ChunkObject(content)
    
    def _create_completion_object(self, response_data: dict):
        """External API 응답을 OpenAI 스타일 completion 객체로 변환"""
        class CompletionObject:
            def __init__(self, content):
                self.choices = [type('Choice', (), {
                    'message': type('Message', (), {'content': content})()
                })()]
        
        # External API 응답에서 content 추출 (실제 응답 구조에 따라 조정 필요)
        content = response_data.get('content', '') or response_data.get('text', '') or response_data.get('response', '')
        return CompletionObject(content)
    
    async def create_title_completion(self, message: str):
        """Create title completion using OpenAIProvider (External API는 타이틀만 OpenAI 사용)"""
        try:
            # OpenAIProvider를 직접 생성해서 타이틀 생성 (설정에서 값 가져오기)
            from src.config.simple_settings import settings
            
            openai_provider = OpenAIProvider(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
            )
            
            # OpenAIProvider의 create_title_completion 사용
            return await openai_provider.create_title_completion(message)
            
        except Exception as e:
            logger.error("External API title generation error: " + str(e))
            raise HandledException(ResponseCode.CHAT_AI_RESPONSE_ERROR, e=e)
    
    def process_stream_chunk(self, chunk) -> str:
        """Process External API streaming chunk and extract content"""
        if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content is not None:
                return delta.content
        return None


class LLMProviderFactory:
    """Factory class for creating LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: str = None, chat_crud=None, user_crud=None) -> BaseLLMProvider:
        """Create LLM provider based on configuration"""
        
        # 환경 변수에서 제공자 타입 가져오기
        if not provider_type:
            provider_type = os.getenv("LLM_PROVIDER", "openai").lower()
        
        logger.info("Creating LLM provider: " + str(provider_type))
        
        if provider_type == "openai":
            return LLMProviderFactory._create_openai_provider()
        elif provider_type == "azure_openai":
            return LLMProviderFactory._create_azure_openai_provider()
        elif provider_type == "external_api":
            return LLMProviderFactory._create_external_api_provider(chat_crud, user_crud)
        else:
            raise HandledException(
                ResponseCode.LLM_CONFIG_ERROR, 
                msg="Unsupported LLM provider: " + str(provider_type) + ". Supported providers: openai, azure_openai, external_api"
            )
    
    @staticmethod
    def _create_openai_provider() -> OpenAIProvider:
        """Create OpenAI provider"""
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        
        return OpenAIProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    @staticmethod
    def _create_azure_openai_provider() -> AzureOpenAIProvider:
        """Create Azure OpenAI provider"""
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        max_tokens = int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "1000"))
        temperature = float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7"))
        
        return AzureOpenAIProvider(
            api_key=api_key,
            endpoint=endpoint,
            deployment_name=deployment_name,
            api_version=api_version,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    @staticmethod
    def _create_external_api_provider(chat_crud=None, user_crud=None) -> ExternalAPIProvider:
        """Create External API provider"""
        api_url = os.getenv("EXTERNAL_API_URL")
        authorization_header = os.getenv("EXTERNAL_API_AUTHORIZATION")
        max_tokens = int(os.getenv("EXTERNAL_API_MAX_TOKENS", "1000"))
        temperature = float(os.getenv("EXTERNAL_API_TEMPERATURE", "0.7"))
        
        return ExternalAPIProvider(
            api_url=api_url,
            authorization_header=authorization_header,
            max_tokens=max_tokens,
            temperature=temperature,
            chat_crud=chat_crud,
            user_crud=user_crud
        )
