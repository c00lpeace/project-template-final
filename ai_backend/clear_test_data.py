# _*_ coding: utf-8 _*_
"""PLC Tree API 테스트 데이터 삭제 (간단 버전)"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models.master_models import (
    PlantMaster,
    ProcessMaster,
    LineMaster,
    EquipmentGroupMaster,
)
from src.database.models.plc_models import PLC

# ⚠️ 여기에 데이터베이스 URL을 입력하세요!
# 예시: "postgresql://postgres:postgres@localhost:5432/mydb"
DATABASE_URL = "postgresql://사용자명:비밀번호@localhost:5432/데이터베이스명"


def main():
    """테스트 데이터 삭제"""
    
    # 데이터베이스 URL 확인
    if "사용자명" in DATABASE_URL or "비밀번호" in DATABASE_URL:
        print("=" * 60)
        print("❌ 에러: 데이터베이스 URL을 설정하지 않았습니다!")
        print("=" * 60)
        print("\n이 파일을 열어서 20번째 줄의 DATABASE_URL을 수정하세요:")
        print('DATABASE_URL = "postgresql://사용자:비번@호스트:포트/DB명"')
        print("\n예시:")
        print('DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/mydb"')
        print("=" * 60)
        return
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("테스트 데이터 삭제 시작")
        print("=" * 60)
        print("\n⚠️  주의: 이 작업은 되돌릴 수 없습니다!")
        
        # 확인 메시지
        confirm = input("\n정말로 테스트 데이터를 삭제하시겠습니까? (yes/no): ")
        
        if confirm.lower() != "yes":
            print("\n작업이 취소되었습니다.")
            return
        
        print("\n삭제 중...")
        
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
        
        print("\n" + "=" * 60)
        print("✅ 테스트 데이터 삭제 완료!")
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
