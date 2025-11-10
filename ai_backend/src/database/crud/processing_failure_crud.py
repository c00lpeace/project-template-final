# _*_ coding: utf-8 _*_
"""ProcessingFailure CRUD operations with database."""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

# 공통 모듈 사용
from shared_core import ProcessingFailure
from shared_core import ProcessingFailureCRUD as BaseProcessingFailureCRUD

logger = logging.getLogger(__name__)


class ProcessingFailureCRUD(BaseProcessingFailureCRUD):
    """ProcessingFailure 관련 CRUD 작업을 처리하는 클래스 (FastAPI 전용 확장)"""

    def __init__(self, db: Session):
        super().__init__(db)

    def create_failure(self, *args, **kwargs) -> ProcessingFailure:
        """실패 정보 생성 (FastAPI 예외 처리)"""
        try:
            return super().create_failure(*args, **kwargs)
        except Exception as e:
            logger.error(f"실패 정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_failure(self, failure_id: str) -> Optional[ProcessingFailure]:
        """실패 정보 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_failure(failure_id)
        except Exception as e:
            logger.error(f"실패 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_program_failures(
        self,
        program_id: str,
        failure_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ProcessingFailure]:
        """프로그램의 실패 정보 목록 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_program_failures(
                program_id=program_id,
                failure_type=failure_type,
                status=status,
            )
        except Exception as e:
            logger.error(f"프로그램 실패 정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_pending_failures(
        self,
        failure_type: Optional[str] = None,
        max_retry_count: Optional[int] = None,
    ) -> List[ProcessingFailure]:
        """재시도 대기 중인 실패 정보 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_pending_failures(
                failure_type=failure_type,
                max_retry_count=max_retry_count,
            )
        except Exception as e:
            logger.error(f"재시도 대기 실패 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_failure_status(
        self,
        failure_id: str,
        status: str,
        error_message: Optional[str] = None,
        resolved_by: Optional[str] = None,
    ) -> bool:
        """실패 정보 상태 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_failure_status(
                failure_id=failure_id,
                status=status,
                error_message=error_message,
                resolved_by=resolved_by,
            )
        except Exception as e:
            logger.error(f"실패 정보 상태 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def increment_retry_count(self, failure_id: str) -> bool:
        """재시도 횟수 증가 (FastAPI 예외 처리)"""
        try:
            return super().increment_retry_count(failure_id)
        except Exception as e:
            logger.error(f"재시도 횟수 증가 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def mark_as_resolved(self, failure_id: str, resolved_by: str = "manual") -> bool:
        """실패 정보를 해결됨으로 표시 (FastAPI 예외 처리)"""
        try:
            return super().mark_as_resolved(failure_id, resolved_by)
        except Exception as e:
            logger.error(f"실패 정보 해결 처리 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_failure(self, failure_id: str) -> bool:
        """실패 정보 삭제 (FastAPI 예외 처리)"""
        try:
            return super().delete_failure(failure_id)
        except Exception as e:
            logger.error(f"실패 정보 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
