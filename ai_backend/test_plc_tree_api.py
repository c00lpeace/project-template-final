# _*_ coding: utf-8 _*_
"""PLC Tree API 테스트 클라이언트"""
import json
import requests
from datetime import datetime


def test_plc_tree_api():
    """PLC Tree API 테스트"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("PLC Tree API 테스트 시작")
    print("=" * 60)
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"서버: {base_url}")
    print("=" * 60)
    
    # 1. 활성 PLC만 조회
    print("\n[테스트 1] 활성 PLC만 조회 (is_active=true)")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{base_url}/v1/plc/tree",
            params={"is_active": True},
            timeout=10
        )
        
        print(f"✓ HTTP Status: {response.status_code}")
        print(f"✓ Response Time: {response.elapsed.total_seconds():.3f}초")
        
        if response.status_code == 200:
            data = response.json()
            
            # 통계 계산
            plant_count = len(data.get("data", []))
            process_count = sum(
                len(plant.get("procList", [])) 
                for plant in data.get("data", [])
            )
            line_count = sum(
                len(proc.get("lineList", []))
                for plant in data.get("data", [])
                for proc in plant.get("procList", [])
            )
            plc_count = sum(
                len(unit.get("info", []))
                for plant in data.get("data", [])
                for proc in plant.get("procList", [])
                for line in proc.get("lineList", [])
                for eq_grp in line.get("eqGrpList", [])
                for unit in eq_grp.get("unitList", [])
            )
            
            print(f"✓ Plant: {plant_count}개")
            print(f"✓ Process: {process_count}개")
            print(f"✓ Line: {line_count}개")
            print(f"✓ 활성 PLC: {plc_count}개")
            
            # JSON 출력 (일부만)
            print("\n응답 데이터 (일부):")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
            
        else:
            print(f"✗ 실패: {response.status_code}")
            print(f"  에러: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print("  명령: uvicorn src.main:app --reload")
        return
    except Exception as e:
        print(f"✗ 에러 발생: {str(e)}")
        return
    
    # 2. 모든 PLC 조회 (비활성 포함)
    print("\n\n[테스트 2] 모든 PLC 조회 (is_active=false)")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{base_url}/v1/plc/tree",
            params={"is_active": False},
            timeout=10
        )
        
        print(f"✓ HTTP Status: {response.status_code}")
        print(f"✓ Response Time: {response.elapsed.total_seconds():.3f}초")
        
        if response.status_code == 200:
            data = response.json()
            
            # 통계 계산
            plc_count = sum(
                len(unit.get("info", []))
                for plant in data.get("data", [])
                for proc in plant.get("procList", [])
                for line in proc.get("lineList", [])
                for eq_grp in line.get("eqGrpList", [])
                for unit in eq_grp.get("unitList", [])
            )
            
            print(f"✓ 전체 PLC: {plc_count}개")
            
        else:
            print(f"✗ 실패: {response.status_code}")
            
    except Exception as e:
        print(f"✗ 에러 발생: {str(e)}")
    
    # 3. 성능 테스트
    print("\n\n[테스트 3] 성능 측정 (10회 반복)")
    print("-" * 60)
    
    try:
        times = []
        for i in range(10):
            response = requests.get(
                f"{base_url}/v1/plc/tree",
                params={"is_active": True},
                timeout=10
            )
            times.append(response.elapsed.total_seconds())
            print(f"  실행 {i+1}: {times[-1]:.3f}초")
        
        print(f"\n✓ 평균: {sum(times) / len(times):.3f}초")
        print(f"✓ 최소: {min(times):.3f}초")
        print(f"✓ 최대: {max(times):.3f}초")
        
    except Exception as e:
        print(f"✗ 에러 발생: {str(e)}")
    
    # 4. 엣지 케이스 테스트
    print("\n\n[테스트 4] 엣지 케이스 테스트")
    print("-" * 60)
    
    # 4-1. 잘못된 파라미터
    print("\n4-1. 잘못된 파라미터 (is_active=invalid)")
    try:
        response = requests.get(
            f"{base_url}/v1/plc/tree",
            params={"is_active": "invalid"},
            timeout=10
        )
        print(f"  Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  ✓ 올바르게 에러 반환")
        else:
            print(f"  ✗ 에러를 반환해야 함")
    except Exception as e:
        print(f"  ✗ 예외 발생: {str(e)}")
    
    # 최종 요약
    print("\n\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)
    print("\n다음 단계:")
    print("  1. Swagger UI에서 확인: http://localhost:8000/docs")
    print("  2. 응답 데이터 구조 확인")
    print("  3. 프론트엔드 연동")
    print("=" * 60)


if __name__ == "__main__":
    test_plc_tree_api()
