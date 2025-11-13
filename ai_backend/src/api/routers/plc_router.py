# _*_ coding: utf-8 _*_
"""PLC Management API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.core.dependencies import get_db
from src.database.crud.plc_crud import PLCCRUD
from src.api.services.plc_tree_service import PLCTreeService
from src.types.response.plc_response import (
    PLCBasicInfo,
    PLCListResponse,
    PLCListItem,
    PLCMappingRequest,
    PLCMappingResponse,
    PLCTreeResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plc", tags=["plc-management"])


@router.get(
    "/tree",
    response_model=PLCTreeResponse,
    summary="PLC 트리 구조 조회",
    description="""
    PLC 목록을 계층적 트리 구조로 조회합니다.
    
    **화면 용도:** PLC 관리 화면의 트리 뷰
    
    **계층 구조:**
    - Plant (공장)
      - Process (공정)
        - Line (라인)
          - Equipment Group (장비 그룹)
            - Unit (호기)
              - PLC 정보 (plc_id, create_dt, user)
    
    **필터링:**
    - `is_active`: 활성 PLC만 조회 (기본값: True)
    
    **정렬:**
    - Master 테이블의 display_order로 자동 정렬
    - Plant -> Process -> Line -> Equipment Group -> Unit 순서
    
    **응답 데이터:**
    - 계층적 트리 구조 (JSON)
    - 각 레벨에 이름 포함
    - 최하위에 PLC 상세 정보
    
    **사용 예시:**
    - 전체 트리: `GET /plc/tree`
    - 비활성 포함: `GET /plc/tree?is_active=false`
    """,
)
def get_plc_tree(
    is_active: bool = Query(
        True, description="활성 PLC만 조회 (기본값: True)"
    ),
    db: Session = Depends(get_db),
):
    """
    PLC 트리 구조 조회

    PLC 목록을 Plant -> Process -> Line -> Equipment Group -> Unit 계층으로 반환합니다.
    """
    try:
        plc_crud = PLCCRUD(db)
        
        # SQL JOIN으로 모든 데이터 한 번에 조회
        rows = plc_crud.get_plc_tree_data(is_active=is_active)
        
        # 트리 구조로 변환
        tree_response = PLCTreeService.build_plc_tree(rows)
        
        return tree_response
        
    except Exception as e:
        logger.error("PLC 트리 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 트리 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get("/{plc_id}", response_model=PLCBasicInfo)
def get_plc_by_id(
    plc_id: str,
    db: Session = Depends(get_db),
):
    """
    PLC 정보 조회 (ID로)

    - plc_id: PLC의 ID (Primary Key)
    - is_active가 true인 경우에만 조회합니다.
    - 기본 정보만 반환합니다 (id, plc_id, plc_name, 계층 구조, program_id).
    """
    try:
        plc_crud = PLCCRUD(db)
        plc = plc_crud.get_plc(plc_id)

        if not plc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PLC를 찾을 수 없습니다. ID: {plc_id}",
            )

        if not plc.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"비활성화된 PLC입니다. ID: {plc_id}",
            )

        # program_id 변경 여부 체크
        program_id_changed = (
            plc.previous_program_id is not None
            and plc.previous_program_id != plc.program_id
        )

        return PLCBasicInfo(
            id=plc.id,
            plc_id=plc.plc_id,
            plc_name=plc.plc_name,
            plant=plc.plant,
            process=plc.process,
            line=plc.line,
            equipment_group=plc.equipment_group,
            unit=plc.unit,
            program_id=plc.program_id,
            program_id_changed=program_id_changed,
            previous_program_id=plc.previous_program_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PLC 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get(
    "",
    response_model=PLCListResponse,
    summary="PLC 기준 정보 목록 조회",
    description="""
    PLC 기준 정보 목록을 검색, 필터링, 페이지네이션, 정렬 기능으로 조회합니다.
    
    **화면 용도:** PLC 관리 화면의 PLC 기준 정보 테이블
    
    **필터링 기능:**
    - `plant_id`: Plant ID로 필터링
    - `process_id`: 공정 ID로 필터링
    - `line_id`: Line ID로 필터링
    - `equipment_group_id`: 장비 그룹 ID로 필터링
    
    **검색 기능:**
    - `plc_id`: PLC ID로 검색
    - `plc_name`: PLC 명으로 검색
    
    **페이지네이션:**
    - `page`: 페이지 번호 (기본값: 1, 최소: 1)
    - `page_size`: 페이지당 항목 수 (기본값: 10, 최소: 1, 최대: 100)
    
    **정렬:**
    - `sort_by`: 정렬 기준 (기본값: `plc_id`)
      - `plc_id`: PLC ID
      - `plc_name`: PLC 명
      - `create_dt`: 생성일시
    - `sort_order`: 정렬 순서 (기본값: `asc`)
      - `asc`: 오름차순
      - `desc`: 내림차순
    
    **응답 데이터:**
    - PLC 목록 (ID, PLC ID, PLC 명, 계층 구조 정보, 매핑된 PGM ID, 매핑 정보 등)
    - 전체 개수 및 페이지 정보
    
    **사용 예시:**
    - 전체 목록: `GET /plc?page=1&page_size=10`
    - 계층별 필터링: `GET /plc?plant_id=plant001&process_id=process001`
    - 검색: `GET /plc?plc_name=PLC001`
    """,
)
def get_plc_list(
    plant_id: Optional[str] = Query(None, description="Plant ID로 필터링", example="plant001"),
    process_id: Optional[str] = Query(None, description="공정 ID로 필터링", example="process001"),
    line_id: Optional[str] = Query(None, description="Line ID로 필터링", example="line001"),
    equipment_group_id: Optional[str] = Query(
        None, description="장비 그룹 ID로 필터링", example="equipment001"
    ),
    plc_id: Optional[str] = Query(None, description="PLC ID로 검색", example="plc001"),
    plc_name: Optional[str] = Query(None, description="PLC 명으로 검색", example="PLC001"),
    page: int = Query(1, ge=1, description="페이지 번호", example=1),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수", example=10),
    sort_by: str = Query(
        "plc_id",
        description="정렬 기준 (plc_id, plc_name, create_dt)",
        example="plc_id",
    ),
    sort_order: str = Query("asc", description="정렬 순서 (asc, desc)", example="asc"),
    db: Session = Depends(get_db),
):
    """
    PLC 기준 정보 목록 조회 (검색, 필터링, 페이지네이션, 정렬)

    화면: PLC 관리 화면의 PLC 기준 정보 테이블
    - Plant, 공정, Line, 장비 그룹, PLC ID, PLC 명으로 검색/필터링
    - 매핑된 PGM ID, 등록자(매핑일시) 표시
    """
    try:
        plc_crud = PLCCRUD(db)
        plcs, total_count = plc_crud.get_plcs(
            plant_id=plant_id,
            process_id=process_id,
            line_id=line_id,
            equipment_group_id=equipment_group_id,
            plc_id=plc_id,
            plc_name=plc_name,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Master 테이블과 조인하여 계층 구조 정보 조회
        items = []
        for plc in plcs:
            # 스냅샷 ID로 계층 구조 정보 조회
            snapshot_ids = {
                "plant_id": plc.plant_id_snapshot,
                "process_id": plc.process_id_snapshot,
                "line_id": plc.line_id_snapshot,
                "equipment_group_id": plc.equipment_group_id_snapshot,
            }
            # 스냅샷 ID로 계층 구조 정보 조회
            hierarchy = None
            if any(snapshot_ids.values()):
                hierarchy = plc_crud._get_hierarchy_with_names(snapshot_ids)

            items.append(
                PLCListItem(
                    id=plc.id,
                    plc_id=plc.plc_id,
                    plc_name=plc.plc_name,
                    plant=hierarchy.get("plant", {}).get("name")
                    if hierarchy
                    else None,
                    process=hierarchy.get("process", {}).get("name")
                    if hierarchy
                    else None,
                    line=hierarchy.get("line", {}).get("name")
                    if hierarchy
                    else None,
                    equipment_group=hierarchy.get("equipment_group", {}).get(
                        "name"
                    )
                    if hierarchy
                    else None,
                    unit=plc.unit,
                    program_id=plc.program_id,
                    mapping_user=plc.mapping_user,
                    mapping_dt=plc.mapping_dt,
                )
            )

        total_pages = (total_count + page_size - 1) // page_size

        return PLCListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("PLC 목록 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 목록 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.put(
    "/mapping",
    response_model=PLCMappingResponse,
    summary="PLC-PGM 매핑 저장",
    description="""
    여러 PLC에 하나의 PGM 프로그램을 매핑합니다.
    
    **화면 용도:** PLC 관리 화면의 매핑 저장 기능
    
    **주요 기능:**
    - 여러 PLC ID에 동일한 PGM 프로그램 매핑
    - 이전 매핑 정보를 `previous_program_id`에 저장 (히스토리 관리)
    - 매핑 사용자 및 매핑 일시 기록
    
    **요청 파라미터:**
    - `plc_ids`: 매핑할 PLC ID 리스트 (배열)
    - `program_id`: 매핑할 PGM 프로그램 ID
    - `mapping_user`: 매핑을 수행한 사용자 ID
    
    **응답:**
    - `success`: 전체 성공 여부
    - `mapped_count`: 성공적으로 매핑된 PLC 개수
    - `failed_count`: 매핑 실패한 PLC 개수
    - `errors`: 실패한 PLC의 오류 정보 리스트
    
    **처리 로직:**
    1. 각 PLC의 현재 `program_id`를 `previous_program_id`에 저장
    2. 새로운 `program_id`로 업데이트
    3. `mapping_user`, `mapping_dt` 업데이트
    
    **예외 상황:**
    - PLC를 찾을 수 없는 경우: 해당 PLC는 실패 처리
    - PGM 프로그램을 찾을 수 없는 경우: 전체 실패
    """,
)
def update_plc_program_mapping(
    request: PLCMappingRequest,
    db: Session = Depends(get_db),
):
    """
    PLC-PGM 매핑 저장

    여러 PLC에 하나의 PGM을 매핑합니다.
    """
    try:
        plc_crud = PLCCRUD(db)
        result = plc_crud.update_plc_program_mapping(
            plc_ids=request.plc_ids,
            program_id=request.program_id,
            mapping_user=request.mapping_user,
        )

        return PLCMappingResponse(
            success=result["failed_count"] == 0,
            mapped_count=result["success_count"],
            failed_count=result["failed_count"],
            errors=result["errors"],
        )
    except Exception as e:
        logger.error("PLC-PGM 매핑 저장 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC-PGM 매핑 저장 중 오류가 발생했습니다: {str(e)}",
        ) from e
