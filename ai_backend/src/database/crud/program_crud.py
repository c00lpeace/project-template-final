# _*_ coding: utf-8 _*_
"""Program CRUD operations with database."""
import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

# 공통 모듈 사용
from shared_core import Program
from shared_core import ProgramCRUD as BaseProgramCRUD

logger = logging.getLogger(__name__)


class ProgramCRUD(BaseProgramCRUD):
    """Program 관련 CRUD 작업을 처리하는 클래스 (FastAPI 전용 확장)"""

    def __init__(self, db: Session):
        super().__init__(db)

    def create_program(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        status: str = Program.STATUS_VALIDATING,
        program_description: Optional[str] = None,
        **kwargs,
    ) -> Program:
        """프로그램 생성 (FastAPI 예외 처리)"""
        try:
            return super().create_program(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                status=status,
                program_description=program_description,
                s3_paths=None,  # 나중에 업데이트
                **kwargs,
            )
        except Exception as e:
            logger.error(f"프로그램 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program_s3_paths(
        self, program_id: str, s3_paths: Dict[str, str]
    ) -> bool:
        """프로그램 S3 경로 업데이트"""
        try:
            return super().update_program_s3_paths(program_id, s3_paths)
        except Exception as e:
            logger.error(f"S3 경로 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program_status(
        self, program_id: str, status: str, error_message: Optional[str] = None
    ) -> bool:
        """프로그램 상태 업데이트"""
        try:
            return super().update_program_status(
                program_id=program_id, status=status, error_message=error_message
            )
        except Exception as e:
            logger.error(f"프로그램 상태 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program_vector_info(
        self,
        program_id: str,
        vector_indexed: bool = True,
        vector_collection_name: Optional[str] = None,
    ) -> bool:
        """프로그램 벡터 정보 업데이트"""
        try:
            return self.update_program(
                program_id=program_id,
                vector_indexed=vector_indexed,
                vector_collection_name=vector_collection_name,
            )
        except Exception as e:
            logger.error(f"프로그램 벡터 정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_program(self, program_id: str) -> Optional[Program]:
        """프로그램 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_program(program_id)
        except Exception as e:
            logger.error(f"프로그램 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_user_programs(self, user_id: str) -> List[Program]:
        """사용자의 프로그램 목록 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_user_programs(user_id)
        except Exception as e:
            logger.error(f"사용자 프로그램 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
