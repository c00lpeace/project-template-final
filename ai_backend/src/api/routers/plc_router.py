# _*_ coding: utf-8 _*_
"""PLC Management API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.core.dependencies import get_db
from src.types.response.plc_response import PLCBasicInfo

from shared_core import PLCCRUD

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plc", tags=["plc-management"])


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
