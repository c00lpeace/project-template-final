# _*_ coding: utf-8 _*_
"""PLC Tree API 테스트 데이터 삽입 스크립트"""
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models.master_models import (
    EquipmentGroupMaster,
    LineMaster,
    PlantMaster,
    ProcessMaster,
)
from src.database.models.plc_models import PLC
from src.utils.uuid_gen import gen

# 데이터베이스 연결 (환경에 맞게 수정)
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/chat_db_final"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def insert_test_data():
    """테스트 데이터 삽입"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("PLC Tree API 테스트 데이터 삽입 시작")
        print("=" * 60)

        # 1. Plant 데이터 삽입
        print("\n[1/5] Plant 데이터 삽입...")
        plants = [
            PlantMaster(
                plant_id=gen(),
                plant_code="PLT001",
                plant_name="공장1",
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            PlantMaster(
                plant_id=gen(),
                plant_code="PLT002",
                plant_name="공장2",
                display_order=2,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
        ]
        db.add_all(plants)
        db.flush()
        print(f"✓ {len(plants)}개 Plant 생성 완료")

        # 2. Process 데이터 삽입
        print("\n[2/5] Process 데이터 삽입...")
        processes = [
            ProcessMaster(
                process_id=gen(),
                process_code="PRC001",
                process_name="공정1",
                plant_id=plants[0].plant_id,
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            ProcessMaster(
                process_id=gen(),
                process_code="PRC002",
                process_name="공정2",
                plant_id=plants[0].plant_id,
                display_order=2,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            ProcessMaster(
                process_id=gen(),
                process_code="PRC003",
                process_name="공정3",
                plant_id=plants[1].plant_id,
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
        ]
        db.add_all(processes)
        db.flush()
        print(f"✓ {len(processes)}개 Process 생성 완료")

        # 3. Line 데이터 삽입
        print("\n[3/5] Line 데이터 삽입...")
        lines = [
            LineMaster(
                line_id=gen(),
                line_code="LN001",
                line_name="라인A",
                process_id=processes[0].process_id,
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            LineMaster(
                line_id=gen(),
                line_code="LN002",
                line_name="라인B",
                process_id=processes[0].process_id,
                display_order=2,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            LineMaster(
                line_id=gen(),
                line_code="LN003",
                line_name="라인C",
                process_id=processes[1].process_id,
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
        ]
        db.add_all(lines)
        db.flush()
        print(f"✓ {len(lines)}개 Line 생성 완료")

        # 4. Equipment Group 데이터 삽입
        print("\n[4/5] Equipment Group 데이터 삽입...")
        equipment_groups = [
            EquipmentGroupMaster(
                equipment_group_id=gen(),
                equipment_group_code="EQ001",
                equipment_group_name="장비그룹A",
                line_id=lines[0].line_id,
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            EquipmentGroupMaster(
                equipment_group_id=gen(),
                equipment_group_code="EQ002",
                equipment_group_name="장비그룹B",
                line_id=lines[0].line_id,
                display_order=2,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
            EquipmentGroupMaster(
                equipment_group_id=gen(),
                equipment_group_code="EQ003",
                equipment_group_name="장비그룹C",
                line_id=lines[1].line_id,
                display_order=1,
                is_active=True,
                create_dt=datetime.now(),
                create_user="system",
            ),
        ]
        db.add_all(equipment_groups)
        db.flush()
        print(f"✓ {len(equipment_groups)}개 Equipment Group 생성 완료")

        # 5. PLC 데이터 삽입
        print("\n[5/5] PLC 데이터 삽입...")
        plcs = [
            # 공장1 -> 공정1 -> 라인A -> 장비그룹A
            PLC(
                id=gen(),
                plc_id="PLC-001",
                plc_name="PLC 라인A 유닛1",
                unit="UNIT-01",
                plant_id_snapshot=plants[0].plant_id,
                process_id_snapshot=processes[0].process_id,
                line_id_snapshot=lines[0].line_id,
                equipment_group_id_snapshot=equipment_groups[0].equipment_group_id,
                plant_id_current=plants[0].plant_id,
                process_id_current=processes[0].process_id,
                line_id_current=lines[0].line_id,
                equipment_group_id_current=equipment_groups[0].equipment_group_id,
                is_active=True,
                create_dt=datetime.now(),
                create_user="admin",
            ),
            PLC(
                id=gen(),
                plc_id="PLC-002",
                plc_name="PLC 라인A 유닛2",
                unit="UNIT-02",
                plant_id_snapshot=plants[0].plant_id,
                process_id_snapshot=processes[0].process_id,
                line_id_snapshot=lines[0].line_id,
                equipment_group_id_snapshot=equipment_groups[0].equipment_group_id,
                plant_id_current=plants[0].plant_id,
                process_id_current=processes[0].process_id,
                line_id_current=lines[0].line_id,
                equipment_group_id_current=equipment_groups[0].equipment_group_id,
                is_active=True,
                create_dt=datetime.now(),
                create_user="admin",
            ),
            # 공장1 -> 공정1 -> 라인A -> 장비그룹B
            PLC(
                id=gen(),
                plc_id="PLC-003",
                plc_name="PLC 라인A 유닛3",
                unit="UNIT-01",
                plant_id_snapshot=plants[0].plant_id,
                process_id_snapshot=processes[0].process_id,
                line_id_snapshot=lines[0].line_id,
                equipment_group_id_snapshot=equipment_groups[1].equipment_group_id,
                plant_id_current=plants[0].plant_id,
                process_id_current=processes[0].process_id,
                line_id_current=lines[0].line_id,
                equipment_group_id_current=equipment_groups[1].equipment_group_id,
                is_active=True,
                create_dt=datetime.now(),
                create_user="admin",
            ),
            # 공장1 -> 공정1 -> 라인B -> 장비그룹C
            PLC(
                id=gen(),
                plc_id="PLC-004",
                plc_name="PLC 라인B 유닛1",
                unit="UNIT-01",
                plant_id_snapshot=plants[0].plant_id,
                process_id_snapshot=processes[0].process_id,
                line_id_snapshot=lines[1].line_id,
                equipment_group_id_snapshot=equipment_groups[2].equipment_group_id,
                plant_id_current=plants[0].plant_id,
                process_id_current=processes[0].process_id,
                line_id_current=lines[1].line_id,
                equipment_group_id_current=equipment_groups[2].equipment_group_id,
                is_active=True,
                create_dt=datetime.now(),
                create_user="admin",
            ),
            # 비활성 PLC
            PLC(
                id=gen(),
                plc_id="PLC-005",
                plc_name="PLC 비활성",
                unit="UNIT-99",
                plant_id_snapshot=plants[0].plant_id,
                process_id_snapshot=processes[0].process_id,
                line_id_snapshot=lines[0].line_id,
                equipment_group_id_snapshot=equipment_groups[0].equipment_group_id,
                plant_id_current=plants[0].plant_id,
                process_id_current=processes[0].process_id,
                line_id_current=lines[0].line_id,
                equipment_group_id_current=equipment_groups[0].equipment_group_id,
                is_active=False,  # 비활성
                create_dt=datetime.now(),
                create_user="admin",
            ),
        ]
        db.add_all(plcs)
        db.commit()
        print(f"✓ {len(plcs)}개 PLC 생성 완료")

        print("\n" + "=" * 60)
        print("✅ 테스트 데이터 삽입 완료!")
        print("=" * 60)
        print(f"\n생성된 데이터:")
        print(f"  - Plant: {len(plants)}개")
        print(f"  - Process: {len(processes)}개")
        print(f"  - Line: {len(lines)}개")
        print(f"  - Equipment Group: {len(equipment_groups)}개")
        print(
            f"  - PLC: {len(plcs)}개 (활성: {len([p for p in plcs if p.is_active])}개)"
        )
        print("\n다음 명령으로 API를 테스트하세요:")
        print("  curl -X GET 'http://localhost:8000/v1/plc/tree?is_active=true'")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


def clear_test_data():
    """테스트 데이터 삭제"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("테스트 데이터 삭제 시작")
        print("=" * 60)

        # 역순으로 삭제 (Foreign Key 제약 때문)
        plc_count = db.query(PLC).delete()
        print(f"✓ PLC {plc_count}개 삭제")

        eq_count = db.query(EquipmentGroupMaster).delete()
        print(f"✓ Equipment Group {eq_count}개 삭제")

        line_count = db.query(LineMaster).delete()
        print(f"✓ Line {line_count}개 삭제")

        process_count = db.query(ProcessMaster).delete()
        print(f"✓ Process {process_count}개 삭제")

        plant_count = db.query(PlantMaster).delete()
        print(f"✓ Plant {plant_count}개 삭제")

        db.commit()

        print("\n✅ 테스트 데이터 삭제 완료!")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PLC Tree API 테스트 데이터 관리")
    parser.add_argument(
        "action",
        choices=["insert", "clear"],
        help="insert: 테스트 데이터 삽입, clear: 테스트 데이터 삭제",
    )

    args = parser.parse_args()

    if args.action == "insert":
        insert_test_data()
    elif args.action == "clear":
        clear_test_data()
