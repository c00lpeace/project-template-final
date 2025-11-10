# Program Registration API Flow

## 전체 플로우 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Client Request                                  │
│  POST /api/v1/programs/register                                        │
│  - program_name: str                                                    │
│  - description: str (optional)                                         │
│  - create_user: str                                                    │
│  - ladder_zip: UploadFile (PLC Ladder Logic ZIP)                       │
│  - classification_xlsx: UploadFile (템플릿 분류체계 XLSX)                │
│  - device_comment_csv: UploadFile (Device 설명 CSV)                      │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_router.py                                    │
│                    ProgramRouter                                        │
│                                                                          │
│  @router.post("/register")  [prefix="/programs"]                        │
│  async def register_program()                                           │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_service.py                                   │
│                    ProgramService                                       │
│                                                                          │
│  async def register_program()                                           │
│    ├─ program_id = gen()                                                │
│    └─ validator.validate_files()  [동기]                                │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_validator.py                                 │
│                    ProgramValidator                                      │
│                                                                          │
│  validate_files()                                                       │
│    ├─ _validate_zip_file()          [ZIP 파일 형식 검증]                │
│    ├─ _validate_xlsx_file()         [XLSX 컬럼 확인]                    │
│    ├─ _validate_csv_file()          [CSV 컬럼 확인]                     │
│    └─ _validate_file_cross_reference() [교차 검증]                      │
│                                                                          │
│  Returns: (is_valid, errors, warnings, checked_files)                   │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
            ┌───────▼───────┐ ┌─────▼──────┐
            │ Validation    │ │ Validation │
            │ PASSED        │ │ FAILED     │
            └───────┬───────┘ └─────┬──────┘
                    │               │
                    │               └─→ 즉시 응답 반환 (DB 저장 없음)
                    │                  status="validation_failed"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_service.py                                   │
│                    ProgramService                                        │
│                                                                          │
│  [검증 통과 시에만 실행]                                                  │
│  [동기 처리]                                                             │
│    ├─ program_crud.create_program()   [RDB 메타데이터 저장]              │
│    │   └─ status: "processing"                                         │
│    └─ db.commit()                                                     │
│                                                                          │
│  [비동기 처리 시작]                                                      │
│    └─ asyncio.create_task(                                              │
│         _process_program_async()                                        │
│       )                                                                 │
│                                                                          │
│  [즉시 응답 반환]                                                         │
│    └─ ProgramUploadResponse                                              │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    API Response (즉시 반환)                              │
│                                                                          │
│  ProgramUploadResponse:                                                 │
│    - program_id: str                                                    │
│    - program_name: str                                                   │
│    - status: "processing"                                               │
│    - validation_result: ValidationResult                              │
│    - message: "유효성 검사를 통과했습니다..."                             │
│    - created_at: datetime                                               │
└─────────────────────────────────────────────────────────────────────────┘

                            │
                            │ (백그라운드에서 계속 진행)
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_service.py                                   │
│                    ProgramService._process_program_async()              │
│                    [비동기 처리]                                         │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────┴───────┐
                    │               │
            ┌───────▼───────┐ ┌─────▼──────┐
            │    Step 1     │ │    Step 2   │ │    Step 3   │
            │  S3 Upload    │ │  DB Save    │ │  Vector DB  │
            │               │ │             │ │  Indexing   │
            └───────┬───────┘ └─────┬──────┘ └─────┬──────┘
                    │               │              │
                    │               │              │
                    ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_uploader.py                                  │
│                    ProgramUploader                                       │
│                                                                          │
│  Step 1: S3 Upload & Unzip                                              │
│    ├─ upload_and_unzip()                                               │
│    │   ├─ _upload_to_s3(ladder_zip)                                    │
│    │   ├─ _unzip_to_s3()          [ZIP 압축 해제]                      │
│    │   ├─ _upload_to_s3(classification_xlsx)                           │
│    │   └─ _upload_to_s3(device_comment_csv)                           │
│    │                                                                     │
│    └─ Returns: s3_paths Dict                                            │
│                                                                          │
│  Step 2: Document 테이블 저장 (program_service에서 처리)                  │
│    ├─ DocumentCRUD.create_document()                                    │
│    │   └─ 각 업로드 파일마다 Document 생성                              │
│    └─ db.commit()                                                      │
│                                                                          │
│  Step 3: 전처리 및 JSON 생성                                            │
│    ├─ ProgramUploader.preprocess_and_create_json()                      │
│    │   ├─ S3에서 압축 해제된 CSV 파일들 다운로드                        │
│    │   ├─ classification_xlsx, device_comment_csv 다운로드              │
│    │   ├─ 전처리 로직 수행                                             │
│    │   ├─ JSON 파일 생성                                               │
│    │   └─ JSON 파일을 S3에 업로드                                      │
│    │                                                                     │
│    └─ Returns: processed_json_files Dict                                │
│                                                                          │
│  Step 4: Document 테이블 저장                                           │
│    ├─ DocumentCRUD.create_document()                                    │
│    │   └─ 각 JSON 파일마다 Document 생성                               │
│    │       ├─ program_id, program_file_type="processed_json" 설정      │
│    │       └─ source_document_id로 ZIP 파일 참조                        │
│    └─ db.commit()                                                      │
│                                                                          │
│  Step 5: Vector DB Indexing                                             │
│    ├─ ProcessingJobCRUD.create_job()  [인덱싱 작업 생성]                  │
│    │   └─ job_type="vector_indexing", status="running"                  │
│    │                                                                     │
│    ├─ request_vector_indexing()                                        │
│    │   └─ HTTP POST to Vector DB Service                                │
│    │                                                                     │
│    └─ ProcessingJobCRUD.update_job_status()                             │
│        ├─ status="completed" (성공 시)                                   │
│        └─ status="failed" (실패 시)                                     │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    program_crud.py                                      │
│                    ProgramCRUD                                           │
│                                                                          │
│  update_program_status()                                                │
│    ├─ status = "completed" (성공 시)                                     │
│    └─ status = "failed" (처리 실패 시)                                  │
│                                                                          │
│  mark_program_as_failed()                                               │
│    └─ error_message 설정                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 클래스 객체 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          API Layer                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ProgramRouter                                                           │
│    - register_program()        [POST /api/v1/programs/register]         │
│    - get_programs()            [GET /api/v1/programs/programs]          │
│    - get_program()             [GET /api/v1/programs/programs/{id}]     │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            │ uses
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  ProgramService                                                          │
│    - __init__(db, uploader)                                              │
│    - register_program()                                                 │
│    - get_program()                                                      │
│    - get_user_programs()                                                │
│    - _process_program_async()                                           │
│                                                                          │
│    Dependencies:                                                         │
│      ├─ ProgramValidator                                                │
│      ├─ ProgramUploader                                                 │
│      ├─ ProgramCRUD                                                     │
│      └─ ProcessingJobCRUD (Vector DB 인덱싱 작업 관리)                    │
└─────────────────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ ProgramValidator  │ │ ProgramUploader   │ │   ProgramCRUD    │
│                   │ │                   │ │                   │
│ validate_files()  │ │ upload_and_       │ │ create_program()  │
│ _validate_zip()   │ │   unzip()         │ │ get_program()     │
│ _validate_xlsx()  │ │ _upload_to_s3()   │ │ update_program_   │
│ _validate_csv()   │ │ _unzip_to_s3()    │ │   status()        │
│ _validate_file_   │ │ request_vector_   │ │ update_program_   │
│   cross_ref()     │ │   indexing()       │ │   s3_paths()      │
└───────────────────┘ └───────────────────┘ └───────────────────┘
                            │
                            │ uses
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  shared_core.models.Program                                             │
│    - program_id: str                                                    │
│    - program_name: str                                                   │
│    - description: str                                                   │
│    - create_dt: datetime                                                │
│    - create_user: str                                                    │
│    - update_dt: datetime                                                │
│    - update_user: str                                                    │
│    - status: str                                                        │
│    - error_message: str                                                  │
│    - completed_at: datetime                                             │
│    - is_used: bool                                                      │
│                                                                          │
│  shared_core.models.ProcessingJob                                      │
│    - job_id: str                                                        │
│    - doc_id: str (Document.document_id 참조)                            │
│    - program_id: str (Program.program_id 참조)                            │
│    - job_type: "vector_indexing"                                        │
│    - status: "running" → "completed"/"failed"                            │
│    - result_data: JSON                                                  │
│    - error_message: str                                                 │
│    - started_at: datetime                                               │
│    - completed_at: datetime                                             │
└─────────────────────────────────────────────────────────────────────────┘
```

## 상세 처리 순서

### Phase 1: 동기 처리 (즉시 응답)

```
1. [Client] POST /api/v1/programs/register
   │
2. [ProgramRouter] register_program() 호출
   │
3. [ProgramService] register_program() 시작
   │   ├─ program_id 생성
   │   └─ ProgramValidator.validate_files() 호출
   │
4. [ProgramValidator] 파일 검증
   │   ├─ ZIP 파일 형식 검증
   │   ├─ XLSX 컬럼 확인 (로직파일명, 분류, 템플릿명)
   │   ├─ CSV 컬럼 확인 (파일명, 디바이스명, 설명)
   │   └─ 교차 검증 (XLSX의 로직파일명이 ZIP에 있는지)
   │
5. [ProgramService] 검증 결과 확인
   │   ├─ 실패: 즉시 에러 응답 반환 (DB 저장하지 않음)
   │   │   └─ status="validation_failed", errors, warnings 반환
   │   └─ 성공: 계속 진행
   │
6. [ProgramCRUD] create_program() - RDB 메타데이터 저장
   │   └─ Program 테이블에 메타데이터 저장 (status: "processing")
   │
7. [ProgramService] 비동기 태스크 생성
   │   └─ asyncio.create_task(_process_program_async())
   │
8. [ProgramRouter] 즉시 응답 반환
   └─ ProgramUploadResponse (status: "processing")
```

### Phase 2: 비동기 처리 (백그라운드)

```
[비동기 태스크 시작]
│
├─ Step 1: S3 업로드 및 압축 해제
│   │
│   └─ [ProgramUploader] upload_and_unzip()
│       ├─ ladder_zip → S3 업로드
│       ├─ ladder_zip → 압축 해제 → S3 업로드
│       ├─ classification_xlsx → S3 업로드
│       └─ device_comment_csv → S3 업로드
│
├─ Step 2: Document 테이블 저장 (업로드된 파일들)
│   │
│   └─ [DocumentCRUD] create_document()
│       ├─ 각 업로드 파일마다 Document 생성
│       ├─ program_id, program_file_type 설정
│       └─ ladder_logic, comment, template 파일 저장
│
├─ Step 3: 전처리 및 JSON 생성
│   │
│   └─ [ProgramUploader] preprocess_and_create_json()
│       ├─ ZIP 압축 해제된 CSV 파일들 다운로드
│       ├─ classification_xlsx, device_comment_csv 다운로드
│       ├─ 전처리 로직 수행
│       ├─ JSON 파일 생성
│       └─ JSON 파일을 S3에 업로드
│           └─ S3: programs/{id}/processed/*.json
│
├─ Step 4: Document 테이블 저장
│   │
│   └─ [DocumentCRUD] create_document()
│       ├─ 각 JSON 파일마다 Document 생성
│       ├─ file_type="application/json"
│       ├─ program_id, program_file_type="processed_json" 설정
│       ├─ source_document_id로 ZIP 파일 참조
│       └─ Document 테이블에 저장 (벡터 인덱싱 대상)
│
└─ Step 5: Vector DB 인덱싱
    │
    ├─ [ProcessingJobCRUD] create_job() - 인덱싱 작업 생성
    │   └─ job_type="vector_indexing", status="running"
    │   └─ doc_id: Document.document_id (각 JSON 파일별)
    │   └─ program_id: Program.program_id 설정
    │
    ├─ [ProgramUploader] request_vector_indexing()
    │   └─ HTTP POST to Vector DB Service
    │   └─ Document 테이블의 JSON 파일들을 인덱싱
    │
    └─ [ProcessingJobCRUD] update_job_status()
        ├─ 성공: status="completed"
        │   └─ [ProgramCRUD] update_program_status("completed")
        └─ 실패: status="failed"
            ├─ [ProgramCRUD] update_program_status("failed")
            └─ [ProcessingFailureCRUD] create_failure() - 실패 정보 저장
```

## 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Input Files                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ladder_zip.zip          → S3: programs/{id}/ladder_logic.zip           │
│                          → S3: programs/{id}/unzipped/*                 │
│                                                                          │
│  classification.xlsx     → S3: programs/{id}/classification.xlsx       │
│                                                                          │
│  device_comment.csv      → S3: programs/{id}/device_comment.csv        │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Database (Programs Table)                                               │
├─────────────────────────────────────────────────────────────────────────┤
│  program_id: "uuid-123"                                                 │
│  program_name: "Program Name"                                           │
│  description: "Program Description"                                    │
│  create_user: "user123"                                                  │
│  status: "preparing" → "uploading" → "processing" → "embedding" → "completed" │
│  error_message: null                                                     │
│  completed_at: datetime                                                  │
│  is_used: true                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 전처리 및 JSON 생성                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  S3에서 압축 해제된 CSV 파일들 다운로드                                  │
│  classification_xlsx, device_comment_csv 다운로드                        │
│  전처리 로직 수행                                                       │
│  JSON 파일 생성                                                         │
│  → S3: programs/{id}/processed/*.json                                   │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Database (Documents Table)                                             │
├─────────────────────────────────────────────────────────────────────────┤
│  document_id: "doc_1", "doc_2", ... (각 JSON 파일별)                    │
│  document_name: "Program Name_processed_0.json"                         │
│  original_filename: "processed_xxx_0.json"                              │
│  file_key: "programs/{id}/processed/processed_xxx_0.json"              │
│  file_type: "application/json"                                          │
│  upload_path: "s3://bucket/programs/{id}/processed/..."                  │
│  status: "processing"                                                   │
│  program_id: "uuid-123"                                                  │
│  program_file_type: "processed_json"                                     │
│  source_document_id: "doc_ladder_zip" (ZIP 파일 참조)                    │
│  user_id: "user123"                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Database (ProcessingJobs Table)                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  job_id: "vector_indexing_uuid-123_20250101_120000"                      │
│  doc_id: "doc_1", "doc_2", ... (Document.document_id)                   │
│  program_id: "uuid-123"                                                  │
│  job_type: "vector_indexing"                                             │
│  status: "running" → "completed" / "failed"                              │
│  result_data: {"document_id": "doc_1", "status": "completed"}             │
│  error_message: null                                                     │
│  started_at: datetime                                                    │
│  completed_at: datetime                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Vector DB Service                                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  POST /index                                                             │
│  {                                                                       │
│    "document_id": "doc_1",                                               │
│    "s3_path": "s3://bucket/programs/{id}/processed/processed_xxx_0.json" │
│  }                                                                       │
│                                                                          │
│  → Vector DB에 JSON 파일 인덱싱                                          │
│  → 각 Document별로 인덱싱 요청                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 상태 변화

```
Program Status Flow:

[검증 통과] → preparing → uploading → processing → embedding → completed ✅
                    │
                    └─→ failed ❌

[검증 실패] → validation_failed (DB 저장 없음)

상태 값:
- preparing: 준비 중 (기본값)
- uploading: 파일 업로드 중
- processing: 전처리 중
- embedding: 임베딩 중
- completed: 완료
- failed: 실패
```

## 에러 처리

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Validation Error                                                         │
│   → 즉시 응답: status="validation_failed"                                │
│   → errors: ["파일 형식 오류", "컬럼 누락", ...]                         │
│   → DB 저장하지 않음                                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ S3 Upload Error                                                          │
│   → 비동기 처리 중: status="failed"                                      │
│   → error_message: "S3 업로드 실패"                                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ Vector DB Indexing Error                                                 │
│   → 비동기 처리 중: status="failed"                                      │
│   → ProcessingJob 테이블에 작업 기록: status="failed"                    │
│   → Program.error_message: "Vector DB 인덱싱 요청 실패"                   │
│   → ProcessingFailure 테이블에 상세 실패 정보 저장                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## 주요 클래스 의존성

```
ProgramRouter
    └─→ ProgramService
            ├─→ ProgramValidator
            ├─→ ProgramUploader
            │       ├─ upload_and_unzip()
            │       ├─ preprocess_and_create_json()
            │       └─ request_vector_indexing()
            ├─→ ProgramCRUD
            │       └─→ Program (Model)
            ├─→ DocumentCRUD
            │       └─→ Document (Model)
            └─→ ProcessingJobCRUD
                    └─→ ProcessingJob (Model)
```

## 비동기 처리 타임라인

```
Time  │
      │
  0s  │ [Client] 요청 전송
      │ [Server] 유효성 검사 (동기)
      │ [Server] DB 저장 (동기)
      │ [Server] 응답 반환 (status: "processing")
      │
      │ [백그라운드] 비동기 태스크 시작
      │
  1s  │ [Step 1] S3 업로드 시작
      │
  5s  │ [Step 1] S3 업로드 완료
      │ [Step 2] DB 저장 시작
      │
  6s  │ [Step 2] DB 저장 완료
      │ [Step 3] 전처리 시작 (ZIP 압축 해제 파일들)
      │
 15s  │ [Step 3] 전처리 완료 (JSON 파일 생성)
      │ [Step 4] Document 테이블 저장 시작
      │
 16s  │ [Step 4] Document 테이블 저장 완료
      │ [Step 5] ProcessingJob 생성 (status: "running")
      │ [Step 5] Vector DB 인덱싱 요청 (Document의 JSON 파일들)
      │
 20s  │ [Step 5] Vector DB 인덱싱 완료
      │ [Server] ProcessingJob 업데이트 (status: "completed")
      │ [Server] Program status 업데이트: "completed"
      │
      │ [Client] GET /api/v1/programs/{id} → status 확인 가능
```

