# _*_ coding: utf-8 _*_
"""PLC response models."""
from datetime import datetime
from typing import Any, Dict, List, Optional

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


class PLCListItem(BaseModel):
    """PLC 목록 항목 (매핑 화면용)"""

    id: str = Field(..., description="PLC ID (Primary Key)")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    plant: Optional[str] = Field(None, description="Plant")
    process: Optional[str] = Field(None, description="공정")
    line: Optional[str] = Field(None, description="Line")
    equipment_group: Optional[str] = Field(None, description="장비 그룹")
    unit: Optional[str] = Field(None, description="호기")
    program_id: Optional[str] = Field(
        None, description="매핑된 PGM ID"
    )
    mapping_user: Optional[str] = Field(None, description="매핑 등록자")
    mapping_dt: Optional[datetime] = Field(None, description="매핑 일시")

    class Config:
        from_attributes = True


class PLCListResponse(BaseModel):
    """PLC 목록 응답"""

    items: List[PLCListItem] = Field(..., description="PLC 목록")
    total_count: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")


class ProgramMappingItem(BaseModel):
    """PGM 프로그램 매핑용 항목 (간단한 정보)"""

    program_id: str = Field(..., description="프로그램 ID (PGM ID)")
    program_name: str = Field(..., description="프로그램 제목")
    ladder_file_count: int = Field(
        default=0, description="Ladder 파일 개수"
    )
    comment_file_count: int = Field(
        default=0, description="Comment 파일 개수"
    )
    create_user: str = Field(..., description="등록자")
    create_dt: datetime = Field(..., description="등록일시")

    class Config:
        from_attributes = True


class ProgramMappingListResponse(BaseModel):
    """PGM 프로그램 매핑용 목록 응답"""

    items: List[ProgramMappingItem] = Field(
        ..., description="프로그램 목록"
    )
    total_count: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")


class PLCMappingRequest(BaseModel):
    """PLC-PGM 매핑 저장 요청"""

    plc_ids: List[str] = Field(
        ..., description="매핑할 PLC ID 리스트", min_items=1
    )
    program_id: str = Field(..., description="매핑할 PGM ID")
    mapping_user: str = Field(..., description="매핑 사용자")


class PLCMappingResponse(BaseModel):
    """PLC-PGM 매핑 저장 응답"""

    success: bool = Field(..., description="성공 여부")
    mapped_count: int = Field(..., description="매핑된 PLC 개수")
    failed_count: int = Field(..., description="실패한 PLC 개수")
    errors: List[str] = Field(
        default_factory=list, description="에러 메시지 리스트"
    )


# ============================================================================
# PLC Tree 구조 Response Models
# ============================================================================


class PLCTreeInfo(BaseModel):
    """PLC 트리 정보 (최하위 노드)"""

    plc_id: str = Field(..., description="PLC ID")
    create_dt: datetime = Field(..., description="생성일시")
    user: str = Field(..., description="생성자")

    class Config:
        from_attributes = True


class PLCTreeUnitNode(BaseModel):
    """Unit 노드"""

    unit: str = Field(..., description="Unit명")
    info: List[PLCTreeInfo] = Field(..., description="PLC 정보 리스트")


class PLCTreeEquipmentNode(BaseModel):
    """Equipment Group 노드"""

    eqGrp: str = Field(..., description="Equipment Group명")
    unitList: List[PLCTreeUnitNode] = Field(..., description="Unit 리스트")


class PLCTreeLineNode(BaseModel):
    """Line 노드"""

    line: str = Field(..., description="Line명")
    eqGrpList: List[PLCTreeEquipmentNode] = Field(
        ..., description="Equipment Group 리스트"
    )


class PLCTreeProcessNode(BaseModel):
    """Process 노드"""

    proc: str = Field(..., description="Process명")
    lineList: List[PLCTreeLineNode] = Field(..., description="Line 리스트")


class PLCTreePlantNode(BaseModel):
    """Plant 노드 (최상위)"""

    plt: str = Field(..., description="Plant명")
    procList: List[PLCTreeProcessNode] = Field(..., description="Process 리스트")


class PLCTreeResponse(BaseModel):
    """PLC 트리 구조 응답"""

    data: List[PLCTreePlantNode] = Field(..., description="Plant 기준 트리 구조")
