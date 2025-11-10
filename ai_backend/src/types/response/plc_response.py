# _*_ coding: utf-8 _*_
"""PLC response models."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class PLCInfo(BaseModel):
    """PLC 정보"""

    id: str = Field(..., description="PLC ID (Primary Key)")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    plant: Optional[str] = Field(None, description="계획")
    process: Optional[str] = Field(None, description="공정")
    line: Optional[str] = Field(None, description="라인")
    equipment_group: Optional[str] = Field(None, description="설비 그룹")
    unit: Optional[str] = Field(None, description="유닛")
    program_id: Optional[str] = Field(None, description="Program ID")
    mapping_dt: Optional[datetime] = Field(None, description="매핑 일시")
    mapping_user: Optional[str] = Field(None, description="매핑 사용자")
    is_active: bool = Field(..., description="활성화 여부")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    create_dt: datetime = Field(..., description="생성 일시")
    create_user: str = Field(..., description="생성 사용자")
    update_dt: Optional[datetime] = Field(None, description="수정 일시")
    update_user: Optional[str] = Field(None, description="수정 사용자")

    class Config:
        from_attributes = True


class PLCBasicInfo(BaseModel):
    """PLC 기본 정보 (is_active=True일 때만 반환)"""

    id: str = Field(..., description="PLC ID (Primary Key)")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    plant: Optional[str] = Field(None, description="계획")
    process: Optional[str] = Field(None, description="공정")
    line: Optional[str] = Field(None, description="라인")
    equipment_group: Optional[str] = Field(None, description="설비 그룹")
    unit: Optional[str] = Field(None, description="유닛")
    program_id: Optional[str] = Field(None, description="Program ID")
    program_id_changed: bool = Field(
        False,
        description="Program ID 변경 여부 (previous_program_id와 다를 경우 True)",
    )
    previous_program_id: Optional[str] = Field(None, description="이전 Program ID")

    class Config:
        from_attributes = True
