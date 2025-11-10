# _*_ coding: utf-8 _*_
"""Program request models."""
from typing import Optional

from pydantic import BaseModel, Field


class ProgramUploadRequest(BaseModel):
    """프로그램 업로드 요청 모델"""

    program_title: str = Field(
        ..., min_length=1, max_length=200, description="프로그램 제목"
    )
    program_description: Optional[str] = Field(
        default=None, max_length=1000, description="프로그램 설명"
    )
    user_id: str = Field(..., min_length=1, max_length=50, description="사용자 ID")

    # 파일들은 FormData로 전달되므로 별도로 정의하지 않음
    # - ladder_zip: UploadFile (PLC Ladder Logic ZIP 파일)
    # - classification_xlsx: UploadFile (템플릿 분류체계 데이터 XLSX)
    # - device_comment_csv: UploadFile (Device 설명 CSV)
