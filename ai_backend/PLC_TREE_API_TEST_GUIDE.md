# 🧪 PLC Tree API 테스트 가이드

## 📋 목차
1. [사전 준비](#사전-준비)
2. [테스트 데이터 삽입](#테스트-데이터-삽입)
3. [API 서버 실행](#api-서버-실행)
4. [API 테스트](#api-테스트)
5. [테스트 데이터 삭제](#테스트-데이터-삭제)

---

## 1. 사전 준비

### 환경 변수 설정
`.env` 파일에서 데이터베이스 연결 정보를 확인하세요.

```bash
cd D:\project-template-final\ai_backend
cat .env
```

### 테스트 스크립트 수정
`test_plc_tree_data.py` 파일의 데이터베이스 URL을 수정하세요.

```python
# 17번째 줄 수정
DATABASE_URL = "postgresql://사용자명:비밀번호@호스트:포트/데이터베이스명"

# 예시:
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/mydb"
```

---

## 2. 테스트 데이터 삽입

### 방법 1: Python 스크립트 실행 (권장)

```bash
cd D:\project-template-final\ai_backend

# 가상환경 활성화 (필요시)
# Windows
venv_py312\Scripts\activate
# Linux/Mac
# source venv_py312/bin/activate

# 테스트 데이터 삽입
python test_plc_tree_data.py insert
```

**예상 출력:**
```
============================================================
PLC Tree API 테스트 데이터 삽입 시작
============================================================

[1/5] Plant 데이터 삽입...
✓ 2개 Plant 생성 완료

[2/5] Process 데이터 삽입...
✓ 3개 Process 생성 완료

[3/5] Line 데이터 삽입...
✓ 3개 Line 생성 완료

[4/5] Equipment Group 데이터 삽입...
✓ 3개 Equipment Group 생성 완료

[5/5] PLC 데이터 삽입...
✓ 5개 PLC 생성 완료

============================================================
✅ 테스트 데이터 삽입 완료!
============================================================

생성된 데이터:
  - Plant: 2개
  - Process: 3개
  - Line: 3개
  - Equipment Group: 3개
  - PLC: 5개 (활성: 4개)

다음 명령으로 API를 테스트하세요:
  curl -X GET 'http://localhost:8000/v1/plc/tree?is_active=true'
============================================================
```

### 방법 2: SQL 직접 실행

만약 스크립트 실행이 안 되면, SQL을 직접 실행할 수도 있습니다.

```sql
-- SQL 파일 생성 (선택사항)
-- 필요시 제공 가능
```

---

## 3. API 서버 실행

### FastAPI 서버 시작

```bash
cd D:\project-template-final\ai_backend

# 가상환경 활성화 (필요시)
venv_py312\Scripts\activate

# 서버 실행
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**예상 출력:**
```
INFO:     Will watch for changes in these directories: ['D:\\project-template-final\\ai_backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

서버가 정상적으로 실행되면 다음 URL에 접속 가능합니다:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

---

## 4. API 테스트

### 방법 1: Swagger UI (가장 쉬움) ⭐

1. 브라우저에서 접속: http://localhost:8000/docs

2. 스크롤하여 **"plc-management"** 섹션 찾기

3. **"GET /v1/plc/tree"** 엔드포인트 클릭

4. **"Try it out"** 버튼 클릭

5. **Parameters** 섹션에서:
   - `is_active`: `true` (기본값)

6. **"Execute"** 버튼 클릭

7. **Response** 확인:
   - Status Code: `200`
   - Response Body에 트리 구조 JSON 표시

**예상 응답:**
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
                          "plc_id": "PLC-001",
                          "create_dt": "2025-11-13T10:00:00",
                          "user": "admin"
                        }
                      ]
                    },
                    {
                      "unit": "UNIT-02",
                      "info": [
                        {
                          "plc_id": "PLC-002",
                          "create_dt": "2025-11-13T10:00:00",
                          "user": "admin"
                        }
                      ]
                    }
                  ]
                },
                {
                  "eqGrp": "장비그룹B",
                  "unitList": [
                    {
                      "unit": "UNIT-01",
                      "info": [
                        {
                          "plc_id": "PLC-003",
                          "create_dt": "2025-11-13T10:00:00",
                          "user": "admin"
                        }
                      ]
                    }
                  ]
                }
              ]
            },
            {
              "line": "라인B",
              "eqGrpList": [
                {
                  "eqGrp": "장비그룹C",
                  "unitList": [
                    {
                      "unit": "UNIT-01",
                      "info": [
                        {
                          "plc_id": "PLC-004",
                          "create_dt": "2025-11-13T10:00:00",
                          "user": "admin"
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

### 방법 2: cURL (명령줄)

#### 활성 PLC만 조회
```bash
curl -X GET "http://localhost:8000/v1/plc/tree?is_active=true"
```

#### 모든 PLC 조회 (비활성 포함)
```bash
curl -X GET "http://localhost:8000/v1/plc/tree?is_active=false"
```

#### 응답을 파일로 저장
```bash
curl -X GET "http://localhost:8000/v1/plc/tree?is_active=true" -o plc_tree.json
```

#### JSON 포맷팅 (jq 사용)
```bash
# jq 설치 필요: https://stedolan.github.io/jq/download/
curl -X GET "http://localhost:8000/v1/plc/tree?is_active=true" | jq .
```

---

### 방법 3: Python requests

```python
import requests
import json

# API 호출
response = requests.get(
    "http://localhost:8000/v1/plc/tree",
    params={"is_active": True}
)

# 상태 코드 확인
print(f"Status Code: {response.status_code}")

# 응답 데이터 확인
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"Error: {response.text}")
```

**실행:**
```bash
python test_api.py
```

---

### 방법 4: Postman

1. **Postman** 실행

2. 새 요청 생성:
   - Method: `GET`
   - URL: `http://localhost:8000/v1/plc/tree`

3. **Params** 탭:
   - Key: `is_active`
   - Value: `true`

4. **Send** 클릭

5. 응답 확인

---

### 방법 5: 브라우저 (직접 접속)

브라우저 주소창에 입력:
```
http://localhost:8000/v1/plc/tree?is_active=true
```

JSON이 브라우저에 바로 표시됩니다.

**TIP**: Chrome에 JSON Viewer 확장 프로그램 설치 권장
- [JSON Viewer](https://chrome.google.com/webstore/detail/json-viewer)

---

## 5. 테스트 데이터 삭제

### 테스트 완료 후 데이터 정리

```bash
cd D:\project-template-final\ai_backend

# 가상환경 활성화 (필요시)
venv_py312\Scripts\activate

# 테스트 데이터 삭제
python test_plc_tree_data.py clear
```

**예상 출력:**
```
============================================================
테스트 데이터 삭제 시작
============================================================
✓ PLC 5개 삭제
✓ Equipment Group 3개 삭제
✓ Line 3개 삭제
✓ Process 3개 삭제
✓ Plant 2개 삭제

✅ 테스트 데이터 삭제 완료!
============================================================
```

---

## 🐛 트러블슈팅

### 문제 1: 데이터베이스 연결 실패
**증상:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결:**
1. PostgreSQL이 실행 중인지 확인
2. `.env` 파일의 DB 연결 정보 확인
3. `test_plc_tree_data.py`의 `DATABASE_URL` 수정

---

### 문제 2: Import Error
**증상:**
```
ModuleNotFoundError: No module named 'src'
```

**해결:**
```bash
# ai_backend 디렉토리에서 실행하는지 확인
cd D:\project-template-final\ai_backend
pwd  # 또는 Windows에서 cd

# 가상환경 활성화 확인
which python  # 또는 Windows에서 where python
```

---

### 문제 3: API 서버 실행 안됨
**증상:**
```
Address already in use
```

**해결:**
```bash
# 8000 포트를 사용 중인 프로세스 종료
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

---

### 문제 4: 빈 트리 반환
**증상:**
```json
{
  "data": []
}
```

**해결:**
1. 테스트 데이터가 삽입되었는지 확인
   ```bash
   python test_plc_tree_data.py insert
   ```

2. `is_active=false`로 시도
   ```bash
   curl -X GET "http://localhost:8000/v1/plc/tree?is_active=false"
   ```

3. 데이터베이스 직접 확인
   ```sql
   SELECT COUNT(*) FROM "PLC" WHERE "IS_ACTIVE" = true;
   ```

---

### 문제 5: 500 Internal Server Error
**증상:**
```json
{
  "detail": "PLC 트리 조회 중 오류가 발생했습니다"
}
```

**해결:**
1. 서버 로그 확인
   ```bash
   tail -f ai_backend/logs/app.log
   ```

2. 에러 메시지 확인하여 원인 파악

3. Master 테이블 데이터 확인
   ```sql
   SELECT * FROM "PLANT_MASTER";
   SELECT * FROM "PROCESS_MASTER";
   SELECT * FROM "LINE_MASTER";
   SELECT * FROM "EQUIPMENT_GROUP_MASTER";
   ```

---

## 📊 테스트 체크리스트

### 기능 테스트
- [ ] 활성 PLC만 조회 (`is_active=true`)
- [ ] 모든 PLC 조회 (`is_active=false`)
- [ ] 트리 구조 계층 확인 (Plant → Process → Line → EqGrp → Unit)
- [ ] PLC 정보 확인 (plc_id, create_dt, user)
- [ ] display_order 정렬 확인

### 성능 테스트
- [ ] 응답 시간 측정 (< 1초)
- [ ] 대량 데이터 테스트 (1000+ PLC)

### 에러 테스트
- [ ] 빈 데이터베이스 처리
- [ ] NULL 값 처리
- [ ] 잘못된 파라미터 처리

---

## 🎯 다음 단계

1. ✅ 테스트 데이터 삽입
2. ✅ API 서버 실행
3. ✅ Swagger UI에서 API 테스트
4. ✅ 응답 데이터 확인
5. ⭐ 프론트엔드 연동 준비

---

**작성일**: 2025-11-13
**버전**: 1.0.0
