# ProcessingFailure 테이블 설계

## 개요

프로그램 처리 중 발생한 실패 정보를 별도 테이블로 관리합니다. 기존 `Program.metadata_json`에 저장하던 방식을 테이블 기반으로 변경하여 쿼리 및 관리가 용이하도록 했습니다.

## 테이블 스키마

### ProcessingFailure 테이블

```python
class ProcessingFailure(Base):
    __tablename__ = "PROCESSING_FAILURES"
    
    # 기본 정보
    failure_id: str (PK)
    program_id: str (FK -> PROGRAMS.PROGRAM_ID)
    
    # 실패 정보
    failure_type: str  # preprocessing, document_storage, vector_indexing
    file_path: str (nullable)
    file_index: int (nullable)
    filename: str (nullable)
    s3_path: str (nullable)
    s3_key: str (nullable)
    
    # 에러 정보
    error_message: str (required)
    error_details: JSON (nullable)
    
    # 재시도 정보
    retry_count: int (default: 0)
    max_retry_count: int (default: 3)
    status: str  # pending, retrying, resolved, failed
    
    # 해결 정보
    resolved_at: datetime (nullable)
    last_retry_at: datetime (nullable)
    resolved_by: str (nullable)  # manual, auto, scheduled
    
    # 메타데이터
    metadata_json: JSON (nullable)
    
    # 시간 정보
    created_at: datetime
    updated_at: datetime
```

## 상태 값

### failure_type
- `preprocessing`: 전처리 단계 실패
- `document_storage`: Document 저장 단계 실패
- `vector_indexing`: Vector DB 인덱싱 단계 실패

### status
- `pending`: 재시도 대기 중
- `retrying`: 재시도 중
- `resolved`: 해결됨 (재시도 성공)
- `failed`: 최종 실패 (최대 재시도 횟수 초과)

## 주요 기능

### 1. 실패 정보 저장

#### 전처리 실패
```python
failure_crud.create_failure(
    failure_id=gen(),
    program_id=program_id,
    failure_type=ProcessingFailure.FAILURE_TYPE_PREPROCESSING,
    error_message="전처리 실패",
    file_path="s3://...",
    file_index=0,
    error_details={...}
)
```

#### Document 저장 실패
```python
failure_crud.create_failure(
    failure_id=gen(),
    program_id=program_id,
    failure_type=ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE,
    error_message="Document 생성 실패",
    filename="processed_xxx.json",
    s3_path="s3://...",
    s3_key="programs/.../processed/...",
    error_details={...}
)
```

### 2. 실패 정보 조회

#### 프로그램별 실패 목록
```python
failures = failure_crud.get_program_failures(
    program_id=program_id,
    failure_type="document_storage",  # optional
    status="pending"  # optional
)
```

#### 재시도 대기 중인 실패 목록
```python
pending = failure_crud.get_pending_failures(
    failure_type="document_storage",  # optional
    max_retry_count=3  # optional
)
```

### 3. 재시도 관리

#### 재시도 횟수 증가
```python
failure_crud.increment_retry_count(failure_id)
# 최대 재시도 횟수 초과 시 자동으로 status='failed'로 변경
```

#### 상태 업데이트
```python
failure_crud.update_failure_status(
    failure_id=failure_id,
    status=ProcessingFailure.STATUS_RETRYING,
    error_message="재시도 중..."
)
```

#### 해결 처리
```python
failure_crud.mark_as_resolved(
    failure_id=failure_id,
    resolved_by="manual"  # 또는 "auto", "scheduled"
)
```

## API 엔드포인트

### 1. 실패 정보 조회
```
GET /api/v1/programs/{program_id}/failures?failure_type={type}&user_id={user_id}
```

**응답 예시:**
```json
{
  "program_id": "prog_123",
  "failures": [
    {
      "failure_id": "fail_1",
      "failure_type": "document_storage",
      "filename": "processed_xxx.json",
      "error_message": "Document 생성 실패",
      "retry_count": 1,
      "max_retry_count": 3,
      "status": "pending",
      "created_at": "2025-01-01T12:00:00"
    }
  ],
  "count": 1
}
```

### 2. 재시도 실행
```
POST /api/v1/programs/{program_id}/retry?retry_type={type}&user_id={user_id}
```

## 데이터 흐름

### 실패 발생 시
```
파일 처리 실패
    ↓
ProcessingFailure 테이블에 저장
    ↓
status='pending' (기본값)
retry_count=0
```

### 재시도 시
```
재시도 API 호출
    ↓
ProcessingFailure 테이블에서 status='pending' 조회
    ↓
각 실패에 대해:
    1. retry_count 증가
    2. status='retrying'
    3. 재시도 로직 실행
    4. 성공 → status='resolved'
       실패 → status='pending' (retry_count < max_retry_count)
            → status='failed' (retry_count >= max_retry_count)
```

## 장점

1. **구조화된 데이터**: JSON이 아닌 테이블로 관리하여 쿼리 용이
2. **인덱싱 가능**: program_id, failure_type, status 등으로 인덱싱 가능
3. **재시도 관리**: 재시도 횟수, 상태 등을 명확히 추적
4. **통계 분석**: 실패율, 재시도 성공률 등 집계 가능
5. **모니터링**: 실패 정보를 SQL로 직접 조회 가능

## 기존 방식과의 차이

### 기존 (metadata_json)
- ❌ JSON 구조로 쿼리 어려움
- ❌ 인덱싱 불가
- ❌ 통계 분석 어려움

### 새로운 방식 (ProcessingFailure 테이블)
- ✅ SQL 쿼리 가능
- ✅ 인덱싱 가능
- ✅ 통계 분석 용이
- ✅ 재시도 관리 체계화

## 주요 쿼리 예시

### 재시도 대기 중인 실패 조회
```sql
SELECT * FROM PROCESSING_FAILURES
WHERE status = 'pending'
  AND retry_count < max_retry_count
ORDER BY created_at;
```

### 프로그램별 실패 통계
```sql
SELECT 
    failure_type,
    status,
    COUNT(*) as count,
    AVG(retry_count) as avg_retry_count
FROM PROCESSING_FAILURES
WHERE program_id = ?
GROUP BY failure_type, status;
```

### 재시도 성공률
```sql
SELECT 
    COUNT(CASE WHEN status = 'resolved' THEN 1 END) as resolved,
    COUNT(*) as total,
    ROUND(COUNT(CASE WHEN status = 'resolved' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
FROM PROCESSING_FAILURES
WHERE program_id = ?;
```

