# _*_ coding: utf-8 _*_
"""Program Management API endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from src.api.services.program_service import ProgramService
from src.core.dependencies import get_program_service
from src.types.response.program_response import (
    ProgramInfo,
    ProgramValidationResult,
    RegisterProgramResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/programs", tags=["program-management"])


@router.post("/register", response_model=RegisterProgramResponse)
async def register_program(
    ladder_zip: UploadFile = File(..., description="PLC ladder logic ZIP 파일"),
    classification_xlsx: UploadFile = File(
        ..., description="템플릿 분류체계 데이터 XLSX 파일"
    ),
    device_comment_csv: UploadFile = File(..., description="Device 설명 CSV 파일"),
    program_title: str = Form(..., description="프로그램 제목"),
    program_description: Optional[str] = Form(None, description="프로그램 설명"),
    user_id: str = Form(default="user", description="사용자 ID"),
    program_service: ProgramService = Depends(get_program_service),
):
    """
    프로그램 등록 API

    - ladder_zip: PLC ladder logic 파일들이 포함된 압축 파일
    - classification_xlsx: 템플릿 분류체계 데이터 (로직 파일명 포함)
    - device_comment_csv: ladder 로직에 있는 device 설명

    유효성 검사를 통과하면:
    1. S3에 파일 업로드 및 ZIP 압축 해제 (비동기)
    2. 백엔드 DB에 메타데이터 저장 (비동기)
    3. Vector DB 인덱싱 요청 (비동기)
    """
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리

    result = await program_service.register_program(
        program_title=program_title,
        program_description=program_description,
        user_id=user_id,
        ladder_zip=ladder_zip,
        classification_xlsx=classification_xlsx,
        device_comment_csv=device_comment_csv,
    )

    # 유효성 검사 결과 구성
    validation_result = None
    if result.get("is_valid") and result.get("warnings"):
        validation_result = ProgramValidationResult(
            is_valid=True,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            checked_files=result.get("checked_files", []),
        )
    elif not result.get("is_valid"):
        validation_result = ProgramValidationResult(
            is_valid=False,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            checked_files=result.get("checked_files", []),
        )

    return RegisterProgramResponse(
        status="success" if result.get("is_valid") else "validation_failed",
        message=result.get(
            "message", "프로그램이 등록되었습니다. 백그라운드에서 처리 중입니다."
        ),
        data=ProgramInfo(**result) if result.get("program_id") else None,
        validation_result=validation_result,
    )


@router.get("/programs", response_model=List[ProgramInfo])
async def get_programs(
    user_id: str = Query(default="user", description="사용자 ID"),
    program_service: ProgramService = Depends(get_program_service),
):
    """프로그램 목록 조회"""
    programs = await program_service.get_user_programs(user_id)
    return [ProgramInfo(**p) for p in programs]


@router.get("/programs/{program_id}", response_model=ProgramInfo)
async def get_program(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    program_service: ProgramService = Depends(get_program_service),
):
    """프로그램 정보 조회"""
    program = await program_service.get_program(program_id, user_id)
    return ProgramInfo(**program)


@router.post("/programs/{program_id}/retry")
async def retry_failed_files(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    retry_type: str = Query(
        default="all", description="재시도 타입 (preprocessing, document, all)"
    ),
    program_service: ProgramService = Depends(get_program_service),
):
    """
    실패한 파일 재시도 API

    - preprocessing: 전처리 실패 파일만 재시도
    - document: Document 저장 실패 파일만 재시도
    - all: 모든 실패 파일 재시도
    """
    result = await program_service.retry_failed_files(
        program_id=program_id, user_id=user_id, retry_type=retry_type
    )
    return result


@router.get("/programs/{program_id}/failures")
async def get_program_failures(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    failure_type: Optional[str] = Query(
        default=None,
        description="실패 타입 필터 (preprocessing, document_storage, vector_indexing)",
    ),
    program_service: ProgramService = Depends(get_program_service),
):
    """프로그램의 실패 정보 목록 조회"""
    failures = await program_service.get_program_failures(
        program_id=program_id, user_id=user_id, failure_type=failure_type
    )
    return {"program_id": program_id, "failures": failures, "count": len(failures)}
