# _*_ coding: utf-8 _*_
"""PLC Tree API 테스트 데이터 삽입 (환경변수 자동 로드)"""
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

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


def get_database_url():
    """환경 변수에서 DATABASE_URL 생성"""

    # 방법 1: DATABASE_URL 환경 변수 직접 사용
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # 방법 2: 개별 환경 변수로 구성
    host = os.getenv("DATABASE_HOST") or os.getenv("POSTGRES_HOST") or "localhost"
    port = os.getenv("DATABASE_PORT") or os.getenv("POSTGRES_PORT") or "5432"
    db_name = os.getenv("DATABASE_NAME") or os.getenv("POSTGRES_DB")
    user = os.getenv("DATABASE_USERNAME") or os.getenv("POSTGRES_USER") or "postgres"
    password = os.getenv("DATABASE_PASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not db_name:
        return None

    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        return f"postgresql://{user}@{host}:{port}/{db_name}"


def main():
    """테스트 데이터 삽입"""

    print("=" * 60)
    print("PLC Tree API 테스트 데이터 삽입 시작")
    print("=" * 60)

    # DATABASE_URL 가져오기
    database_url = get_database_url()

    if not database_url:
        print("\n❌ 에러: 데이터베이스 연결 정보를 찾을 수 없습니다!")
        print("\n다음 중 하나를 수행하세요:")
        print("\n방법 1: .env 파일에 다음 변수를 설정")
        print("  DATABASE_URL=postgresql://user:pass@host:port/dbname")
        print("\n방법 2: .env 파일에 개별 변수 설정")
        print("  DB_HOST=localhost")
        print("  DB_PORT=5432")
        print("  DB_NAME=your_database")
        print("  DB_USER=postgres")
        print("  DB_PASSWORD=your_password")
        print("\n방법 3: check_db_config.py를 실행하여 현재 설정 확인")
        print("  python check_db_config.py")
        print("=" * 60)
        return

    # 연결 정보 출력 (비밀번호 마스킹)
    masked_url = database_url
    if "@" in masked_url and ":" in masked_url:
        parts = masked_url.split("://")
        if len(parts) == 2:
            protocol = parts[0]
            rest = parts[1]
            if "@" in rest:
                creds, location = rest.split("@", 1)
                if ":" in creds:
                    user, password = creds.split(":", 1)
                    masked_password = (
                        password[:1] + "*" * (len(password) - 2) + password[-1:]
                        if len(password) > 2
                        else "***"
                    )
                    masked_url = f"{protocol}://{user}:{masked_password}@{location}"

    print(f"\n데이터베이스: {masked_url}")

    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # 연결 테스트
        db.execute("SELECT 1")
        print("✓ 데이터베이스 연결 성공")

    except Exception as e:
        print(f"\n❌ 데이터베이스 연결 실패: {str(e)}")
        print("\n연결 정보를 확인하세요:")
        print("  python check_db_config.py")
        return

    try:
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
        print("\n다음 단계:")
        print("  1. API 서버 실행:")
        print("     uvicorn src.main:app --reload")
        print("\n  2. 브라우저에서 테스트:")
        print("     http://localhost:8000/docs")
        print("\n  3. API 호출:")
        print("     curl -X GET 'http://localhost:8000/v1/plc/tree?is_active=true'")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
