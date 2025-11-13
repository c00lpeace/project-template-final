# _*_ coding: utf-8 _*_
"""PLC Tree Service - PLC 목록을 트리 구조로 변환"""
import logging
from collections import defaultdict
from typing import Any, Dict, List

from src.types.response.plc_response import (
    PLCTreeEquipmentNode,
    PLCTreeInfo,
    PLCTreeLineNode,
    PLCTreePlantNode,
    PLCTreeProcessNode,
    PLCTreeResponse,
    PLCTreeUnitNode,
)

logger = logging.getLogger(__name__)


class PLCTreeService:
    """PLC 트리 구조 변환 서비스"""

    @staticmethod
    def build_plc_tree(rows: List[Any]) -> PLCTreeResponse:
        """
        SQL 조인 결과를 트리 구조로 변환
        
        Args:
            rows: SQL 조인 결과 (PLC + Master 테이블)
            
        Returns:
            PLCTreeResponse: 트리 구조 응답
        """
        # 5단계 중첩 딕셔너리: Plant -> Process -> Line -> EqGrp -> Unit
        tree: Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, List[Dict]]]]]] = (
            defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
                )
            )
        )

        # 데이터 그룹핑
        for row in rows:
            # 이름이 없는 경우 기본값 설정
            plant_name = row.plant_name or "Unknown Plant"
            process_name = row.process_name or "Unknown Process"
            line_name = row.line_name or "Unknown Line"
            eq_grp_name = row.eq_grp_name or "Unknown Equipment"
            unit = row.unit or "Unknown Unit"

            # PLC 정보 추가
            plc_info = {
                "plc_id": row.plc_id,
                "create_dt": row.create_dt,
                "user": row.create_user,
            }

            tree[plant_name][process_name][line_name][eq_grp_name][unit].append(
                plc_info
            )

        # 중첩 딕셔너리를 JSON 구조로 변환
        plant_list = []

        for plant_name, processes in tree.items():
            proc_list = []

            for process_name, lines in processes.items():
                line_list = []

                for line_name, eq_grps in lines.items():
                    eq_grp_list = []

                    for eq_grp_name, units in eq_grps.items():
                        unit_list = []

                        for unit, plc_infos in units.items():
                            # PLCTreeInfo 객체 생성
                            info_list = [
                                PLCTreeInfo(
                                    plc_id=info["plc_id"],
                                    create_dt=info["create_dt"],
                                    user=info["user"],
                                )
                                for info in plc_infos
                            ]

                            unit_list.append(
                                PLCTreeUnitNode(unit=unit, info=info_list)
                            )

                        eq_grp_list.append(
                            PLCTreeEquipmentNode(
                                eqGrp=eq_grp_name, unitList=unit_list
                            )
                        )

                    line_list.append(
                        PLCTreeLineNode(line=line_name, eqGrpList=eq_grp_list)
                    )

                proc_list.append(
                    PLCTreeProcessNode(proc=process_name, lineList=line_list)
                )

            plant_list.append(PLCTreePlantNode(plt=plant_name, procList=proc_list))

        return PLCTreeResponse(data=plant_list)
