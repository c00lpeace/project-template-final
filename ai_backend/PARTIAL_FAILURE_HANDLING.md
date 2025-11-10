# 부분 실패 처리 가이드

## 개요

300개 파일 처리 중 일부 파일이 실패하더라도 나머지 파일 처리를 계속 진행하고, 실패한 파일은 나중에 재시도할 수 있도록 구현했습니다.

## 부분 실패 커버 메커니즘

### 1. 실패 정보 추적

#### 전처리 단계 실패
- `preprocess_and_create_json()`에서 실패한 파일 정보를 반환
- 실패 정보 구조:
  ```json
  {
    "file_path": "s3://...",
    "index": 0,
    "error": "에러 메시지",
    "retry_count": 0,
    "timestamp": "2025-01-01T12:00:00"
  }
  ```

#### Document 저장 단계 실패
- `_process_program_async()`에서 Document 생성 실패 정보 기록
- 실패 정보 구조:
  ```json
  {
    "json_key": "json_file_0",
    "filename": "processed_xxx_0.json",
    "s3_path": "s3://...",
    "source_file_path": "s3://...",
    "source_index": 0,
    "error": "에러 메시지",
    "timestamp": "2025-01-01T12:00:00"
  }
  ```

### 2. 실패 정보 저장

실패한 파일 정보는 `Program.metadata_json`에 저장됩니다:

```json
{
  "preprocessing": {
    "summary": {
      "total": 300,
      "success": 295,
      "failed": 5
    },
    "failed_files": [...]
  },
  "document_storage": {
    "summary": {
      "total": 295,
      "success": 290,
      "failed": 5
    },
    "failed_files": [...]
  },
  "total_expected": 300,
  "total_successful_documents": 290,
  "has_partial_failure": true,
  "retry_history": [
    {
      "retry_type": "document",
      "timestamp": "2025-01-01T13:00:00",
      "results": {
        "document": {
          "retried": 5,
          "success": 3,
          "failed": 2
        }
      }
    }
  ]
}
```

### 3. 재시도 API

#### 엔드포인트
```
POST /api/v1/programs/{program_id}/retry?retry_type={type}&user_id={user_id}
```

#### 파라미터
- `program_id`: 프로그램 ID
- `user_id`: 사용자 ID (쿼리 파라미터)
- `retry_type`: 재시도 타입
  - `preprocessing`: 전처리 실패 파일만 재시도
  - `document`: Document 저장 실패 파일만 재시도
  - `all`: 모든 실패 파일 재시도 (기본값)

#### 응답 예시
```json
{
  "program_id": "prog_123",
  "retry_type": "document",
  "results": {
    "preprocessing": {
      "retried": 0,
      "success": 0,
      "failed": 0
    },
    "document": {
      "retried": 5,
      "success": 3,
      "failed": 2
    }
  },
  "message": "재시도 완료"
}
```

### 4. 재시도 로직

#### Document 저장 재시도
1. `Program.metadata_json`에서 실패한 파일 목록 조회
2. 각 실패 파일에 대해:
   - S3에서 JSON 파일 확인 (이미 업로드되어 있음)
   - Document 재생성 시도
   - 성공/실패 기록
3. 재시도 결과를 `retry_history`에 추가

#### 전처리 재시도 (TODO)
- 실패한 파일만 다시 전처리 수행
- S3 업로드 및 Document 저장

## 사용 예시

### 1. 프로그램 처리 상태 확인

```python
# GET /api/v1/programs/{program_id}
program = await program_service.get_program(program_id, user_id)

# metadata_json에서 실패 정보 확인
metadata = program.get("metadata_json", {})
if metadata.get("has_partial_failure"):
    print(f"부분 실패 발생: 전처리 {metadata['preprocessing']['summary']['failed']}개, "
          f"Document {metadata['document_storage']['summary']['failed']}개")
```

### 2. 실패한 파일 재시도

```python
# POST /api/v1/programs/{program_id}/retry?retry_type=document
result = await program_service.retry_failed_files(
    program_id=program_id,
    user_id=user_id,
    retry_type="document"  # 또는 "preprocessing", "all"
)

print(f"재시도 결과: {result['results']}")
```

### 3. 실패 정보 조회

```python
program = await program_service.get_program(program_id, user_id)
metadata = program.get("metadata_json", {})

# 전처리 실패 파일 목록
preprocessing_failures = metadata.get("preprocessing", {}).get("failed_files", [])

# Document 저장 실패 파일 목록
document_failures = metadata.get("document_storage", {}).get("failed_files", [])

print(f"전처리 실패: {len(preprocessing_failures)}개")
print(f"Document 저장 실패: {len(document_failures)}개")
```

## 처리 흐름

```
1. 파일 처리 시작 (300개)
   │
   ├─ 전처리 단계
   │   ├─ 성공: 295개 → JSON 생성 및 S3 업로드
   │   └─ 실패: 5개 → failed_files에 기록
   │
   ├─ Document 저장 단계
   │   ├─ 성공: 290개 → Document 생성
   │   └─ 실패: 5개 → failed_document_files에 기록
   │
   └─ 실패 정보 저장
       └─ Program.metadata_json에 저장
       
2. 재시도 (필요시)
   │
   ├─ POST /retry?retry_type=document
   │   └─ Document 저장 실패 파일만 재시도
   │
   └─ POST /retry?retry_type=all
       └─ 모든 실패 파일 재시도
```

## 장점

1. **부분 성공 허용**: 일부 파일 실패해도 나머지 파일 처리 계속
2. **실패 추적**: 모든 실패 정보를 DB에 저장하여 추적 가능
3. **선택적 재시도**: 실패한 파일만 재시도 가능
4. **재시도 이력**: 재시도 결과를 `retry_history`에 기록
5. **모니터링**: 실패율 및 재시도 성공률 추적 가능

## 주의사항

1. **재시도 횟수 제한**: 무한 재시도 방지를 위해 최대 재시도 횟수 설정 권장
2. **S3 파일 확인**: Document 재시도 시 S3에 JSON 파일이 존재하는지 확인 필요
3. **전처리 재시도**: 전처리 재시도는 실제 전처리 로직 구현 후 완성
4. **동시성**: 동일 파일에 대한 동시 재시도 방지 필요

