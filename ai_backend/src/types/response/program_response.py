# _*_ coding: utf-8 _*_
"""Program response models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ProgramValidationResult(BaseModel):
    """유효성 검사 결과"""
    is_valid: bool = Field(..., description="유효성 검사 통과 여부")
    errors: list = Field(default_factory=list, description="에러 목록")
    warnings: list = Field(default_factory=list, description="경고 목록")
    checked_files: list = Field(default_factory=list, description="체크된 파일 목록")
    file_count_in_zip: Optional[int] = Field(None, description="ZIP 파일 내 파일 수")
    file_count_in_xlsx: Optional[int] = Field(None, description="XLSX 파일 내 로직 파일명 수")
    matched_files: Optional[list] = Field(None, description="매칭된 파일 목록")
    missing_files: Optional[list] = Field(None, description="누락된 파일 목록")


class ProgramInfo(BaseModel):
    """프로그램 정보"""
    program_id: str = Field(..., description="프로그램 ID")
    program_title: str = Field(..., description="프로그램 제목")
    program_description: Optional[str] = Field(None, description="프로그램 설명")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    status: str = Field(..., description="처리 상태")
    is_valid: Optional[bool] = Field(None, description="유효성 검사 통과 여부")
    errors: Optional[list] = Field(None, description="에러 목록")
    warnings: Optional[list] = Field(None, description="경고 목록")
    checked_files: Optional[list] = Field(None, description="체크된 파일 목록")
    message: Optional[str] = Field(None, description="메시지")
    validation_result: Optional[Dict[str, Any]] = Field(None, description="유효성 검사 결과")
    create_dt: Optional[datetime] = Field(None, description="생성 일시")
    updated_at: Optional[datetime] = Field(None, description="수정 일시")
    
    class Config:
        from_attributes = True


class RegisterProgramResponse(BaseModel):
    """프로그램 등록 응답"""
    status: str = Field(..., description="응답 상태")
    message: str = Field(..., description="응답 메시지")
    data: Optional[ProgramInfo] = Field(None, description="프로그램 정보")
    validation_result: Optional[ProgramValidationResult] = Field(None, description="유효성 검사 결과")

