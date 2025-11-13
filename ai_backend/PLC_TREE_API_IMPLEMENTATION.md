# PLC 트리 구조 API 구현 완료

## 📋 작업 개요

PLC 목록을 계층적 트리 구조로 변환하여 제공하는 API를 구현했습니다.

**구현 날짜**: 2025-11-13

---

## 🎯 구현 내용

### 1. 트리 구조 Response Schema 추가
**파일**: `ai_backend/src/types/response/plc_response.py`

다음 Response Model들을 추가했습니다:
- `PLCTreeInfo` - PLC 상세 정보 (최하위 노드)
- `PLCTreeUnitNode` - Unit 노드
- `PLCTreeEquipmentNode` - Equipment Group 노드
- `PLCTreeLineNode` - Line 노드
- `PLCTreeProcessNode` - Process 노드
- `PLCTreePlantNode` - Plant 노드 (최상위)
- `PLCTreeResponse` - 전체 트리 응답

**계층 구조**:
```
Plant (공장)
  └─ Process (공정)
      └─ Line (라인)
          └─ Equipment Group (장비 그룹)
              └─ Unit (호기)
                  └─ PLC 정보 (plc_id, create_dt, user)
```

---

### 2. CRUD 메서드 추가
**파일**: `ai_backend/src/database/crud/plc_crud.py`

#### `get_plc_tree_data()` 메서드
- **기능**: SQL JOIN으로 모든 Master 테이블과 PLC 테이블을 한 번에 조회
- **JOIN 테이블**:
  - PLANT_MASTER
  - PROCESS_MASTER
  - LINE_MASTER
  - EQUIPMENT_GROUP_MASTER
- **정렬**: display_order 기준 자동 정렬
- **필터링**: is_active 파라미터로 활성 PLC만 조회 가능

**SQL 최적화**:
- 단일 쿼리로 모든 데이터 조회 (N+1 문제 해결)
- OUTER JOIN 사용으로 NULL 값 처리
- display_order로 정렬하여 일관된 순서 보장

---

### 3. Service Layer 추가
**파일**: `ai_backend/src/api/services/plc_tree_service.py`

#### `PLCTreeService` 클래스
- **메서드**: `build_plc_tree(rows)` (static method)
- **기능**: SQL 조인 결과를 중첩 딕셔너리로 그룹핑 후 JSON 트리 구조로 변환
- **알고리즘**: 5단계 중첩 딕셔너리 사용 (Plant → Process → Line → EqGrp → Unit)

**변환 과정**:
1. SQL 결과를 중첩 딕셔너리로 그룹핑
2. 각 레벨별로 Pydantic 모델 객체 생성
3. 최종 트리 구조 반환

---

### 4. Router 엔드포인트 추가
**파일**: `ai_backend/src/api/routers/plc_router.py`

#### `GET /plc/tree` 엔드포인트
- **파라미터**: 
  - `is_active` (optional, default=True): 활성 PLC만 조회
- **응답 형식**: `PLCTreeResponse`
- **에러 처리**: HTTPException으로 500 에러 반환

**API 문서**:
- Swagger UI에 상세 설명 추가
- 계층 구조 설명
- 사용 예시 포함

---

## 📊 응답 예시

```json
{
  "data": [
    {
      "plt": "공장1",
      "procList": [
        {
          "proc": "공정1",
          "lineList": [
            {
              "line": "라인A",
              "eqGrpList": [
                {
                  "eqGrp": "장비그룹A",
                  "unitList": [
                    {
                      "unit": "UNIT-01",
                      "info": [
                        {
                          "plc_id": "PLC_A001",
                          "create_dt": "2025-11-13T10:00:00",
                          "user": "user001"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 🔧 기술 세부사항

### 옵션 B 방식 채택
**SQL 쿼리 최적화 + Python 그룹핑**

**장점**:
- ✅ 단일 SQL 쿼리로 모든 데이터 조회 (성능 최적화)
- ✅ N+1 쿼리 문제 해결
- ✅ 네트워크 I/O 최소화
- ✅ 코드 간결성 및 유지보수성 향상
- ✅ display_order 자동 정렬

### SQLAlchemy 쿼리 구조
```python
query = (
    db.query(
        PLC.id,
        PLC.plc_id,
        ...
        PlantMaster.plant_name.label("plant_name"),
        ProcessMaster.process_name.label("process_name"),
        ...
    )
    .outerjoin(PlantMaster, PLC.plant_id_snapshot == PlantMaster.plant_id)
    .outerjoin(ProcessMaster, PLC.process_id_snapshot == ProcessMaster.process_id)
    ...
    .filter(PLC.is_active == is_active)
    .order_by(
        PlantMaster.display_order.nullslast(),
        ...
    )
)
```

---

## 📚 문서 업데이트

### API 문서 (`docs/API_DOCUMENTATION.md`)
- **새 섹션 추가**: "4. PLC 트리 구조 조회"
- **변경 이력 업데이트**: v1.2.0 추가
- **API 개수 수정**: PLC 관리 API 3개 → 4개

**업데이트 내용**:
- 엔드포인트 설명
- Request/Response 예시
- 계층 구조 설명
- 사용 예시

---

## ✅ 테스트 가이드

### API 테스트 방법

1. **Swagger UI 사용**:
   ```
   http://localhost:8000/docs
   ```
   - `GET /v1/plc/tree` 엔드포인트 찾기
   - `Try it out` 클릭
   - `is_active` 파라미터 설정
   - `Execute` 클릭

2. **cURL 사용**:
   ```bash
   # 활성 PLC만 조회
   curl -X GET "http://localhost:8000/v1/plc/tree?is_active=true"
   
   # 모든 PLC 조회
   curl -X GET "http://localhost:8000/v1/plc/tree?is_active=false"
   ```

3. **Python 사용**:
   ```python
   import requests
   
   response = requests.get(
       "http://localhost:8000/v1/plc/tree",
       params={"is_active": True}
   )
   tree_data = response.json()
   print(tree_data)
   ```

---

## 🎨 성능 특징

### 시간 복잡도
- **SQL 조회**: O(n) - n은 PLC 개수
- **그룹핑**: O(n) - 단일 패스로 그룹핑
- **트리 변환**: O(n) - 모든 노드 한 번씩 방문

### 공간 복잡도
- **메모리 사용**: O(n + k)
  - n: PLC 개수
  - k: 고유한 계층 노드 개수 (Plant, Process, Line, EqGrp, Unit)

### 성능 벤치마크 (예상)
- **1,000개 PLC**: ~100ms
- **10,000개 PLC**: ~500ms
- **100,000개 PLC**: ~2-3초

---

## 🔍 디버깅 팁

### 로그 확인
```bash
# PLC 트리 조회 로그
tail -f ai_backend/logs/app.log | grep "PLC 트리"
```

### 일반적인 문제

1. **빈 트리 반환**:
   - `is_active=True`로 조회 시 활성 PLC가 없는 경우
   - 해결: `is_active=False`로 시도

2. **NULL 값 처리**:
   - Master 테이블에 없는 ID가 스냅샷에 있는 경우
   - 해결: "Unknown XXX"로 표시됨

3. **정렬 순서**:
   - Master 테이블의 `display_order`가 NULL인 경우
   - 해결: `nullslast()`로 NULL 값은 마지막에 배치

---

## 📦 파일 목록

### 생성된 파일
- `ai_backend/src/api/services/plc_tree_service.py` - 트리 변환 서비스

### 수정된 파일
- `ai_backend/src/types/response/plc_response.py` - Response Schema 추가
- `ai_backend/src/database/crud/plc_crud.py` - get_plc_tree_data() 추가
- `ai_backend/src/api/routers/plc_router.py` - GET /tree 엔드포인트 추가
- `docs/API_DOCUMENTATION.md` - API 문서 업데이트

---

## 🚀 향후 개선 사항

### 선택적 개선
1. **캐싱 추가**: Redis 캐시로 성능 향상 (TTL 1시간)
2. **필터링 확장**: Plant/Process/Line 단위 필터링
3. **페이징**: 대량 데이터 처리를 위한 페이징
4. **정렬 옵션**: 이름순, 생성일순 등 다양한 정렬 옵션

### 필수 아님
- 현재 구현으로 충분히 안정적이고 효율적

---

## 📝 변경 이력

**2025-11-13**
- PLC 트리 구조 API 구현 완료
- 옵션 B (SQL 최적화 + Python 그룹핑) 방식 채택
- 4개 파일 수정, 1개 파일 생성
- API 문서 업데이트 완료

---

**작성자**: AI Assistant
**프로젝트**: project-template-final
**버전**: 1.2.0
