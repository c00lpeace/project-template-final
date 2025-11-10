# _*_ coding: utf-8 _*_
"""KnowledgeReference CRUD operations with database."""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

# 공통 모듈 사용
from shared_core import KnowledgeReference
from shared_core import KnowledgeReferenceCRUD as BaseKnowledgeReferenceCRUD

logger = logging.getLogger(__name__)


class KnowledgeReferenceCRUD(BaseKnowledgeReferenceCRUD):
    """KnowledgeReference 관련 CRUD 작업을 처리하는 클래스 (FastAPI 전용 확장)"""

    def __init__(self, db: Session):
        super().__init__(db)

    def create_reference(self, *args, **kwargs) -> KnowledgeReference:
        """Knowledge 참조 정보 생성 (FastAPI 예외 처리)"""
        try:
            return super().create_reference(*args, **kwargs)
        except Exception as e:
            logger.error(f"Knowledge 참조 정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_reference(self, reference_id: str) -> Optional[KnowledgeReference]:
        """Knowledge 참조 정보 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_reference(reference_id)
        except Exception as e:
            logger.error(f"Knowledge 참조 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_latest_reference(self, reference_type: str) -> Optional[KnowledgeReference]:
        """최신 버전 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_latest_reference(reference_type)
        except Exception as e:
            logger.error(f"최신 Knowledge 참조 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_references_by_type(
        self, reference_type: str, include_inactive: bool = False
    ) -> List[KnowledgeReference]:
        """타입별 참조 정보 목록 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_references_by_type(
                reference_type=reference_type, include_inactive=include_inactive
            )
        except Exception as e:
            logger.error(f"타입별 참조 정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_reference(self, *args, **kwargs) -> bool:
        """Knowledge 참조 정보 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_reference(*args, **kwargs)
        except Exception as e:
            logger.error(f"Knowledge 참조 정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def set_as_latest(self, reference_id: str, update_by: Optional[str] = None) -> bool:
        """최신 버전 설정 (FastAPI 예외 처리)"""
        try:
            return super().set_as_latest(reference_id, update_by)
        except Exception as e:
            logger.error(f"최신 버전 설정 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_reference(self, reference_id: str) -> bool:
        """Knowledge 참조 정보 삭제 (FastAPI 예외 처리)"""
        try:
            return super().delete_reference(reference_id)
        except Exception as e:
            logger.error(f"Knowledge 참조 정보 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
