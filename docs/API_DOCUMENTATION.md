# 📡 API 문서

## 목차
- [개요](#개요)
- [인증 및 권한](#인증-및-권한)
- [공통 응답 형식](#공통-응답-형식)
- [채팅 API](#채팅-api)
- [사용자 API](#사용자-api)
- [문서 관리 API](#문서-관리-api)
- [프로그램 관리 API](#프로그램-관리-api)
- [PLC 관리 API](#plc-관리-api)
- [그룹 API](#그룹-api)
- [평가 API](#평가-api)
- [에러 코드](#에러-코드)

---

## 프로그램 관리 API

### 1. 프로그램 등록
**POST** `/v1/programs/register`

**Request (multipart/form-data):**
- `ladder_zip` (required): PLC ladder logic ZIP 파일
- `classification_xlsx` (required): 템플릿 분류체계 XLSX 파일
- `device_comment_csv` (required): Device 설명 CSV 파일
- `program_title` (required): 프로그램 제목
- `program_description` (optional): 프로그램 설명
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "message": "파일 등록 요청하였습니다.",
  "data": {
    "program_id": "pgm_abc123",
    "program_name": "공정1 PLC 프로그램",
    "status": "uploading"
  },
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "checked_files": ["file1.txt", "file2.txt"]
  }
}
```

---

### 2. 프로그램 목록 조회
**GET** `/v1/programs`

**Query Parameters:**
- `program_id` (optional): PGM ID로 검색
- `program_name` (optional): 제목으로 검색
- `status` (optional): 상태 필터링 (preparing/uploading/processing/embedding/completed/failed)
- `create_user` (optional): 작성자 필터링
- `page` (optional): 페이지 번호 (default: 1)
- `page_size` (optional): 페이지당 항목 수 (default: 10, max: 100)
- `sort_by` (optional): 정렬 기준 (default: "create_dt")
- `sort_order` (optional): 정렬 순서 (default: "desc")

**Response:**
```json
{
  "items": [
    {
      "program_id": "pgm_abc123",
      "program_name": "공정1 PLC 프로그램",
      "process_name": "공정1",
      "ladder_file_count": 150,
      "comment_file_count": 1,
      "status": "completed",
      "status_display": "성공",
      "processing_time": "5 min",
      "create_user": "user001",
      "create_dt": "2025-11-13T10:00:00"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

### 3. 프로그램 상세 조회
**GET** `/v1/programs/{program_id}`

**Path Parameters:**
- `program_id` (required): 프로그램 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "program_id": "pgm_abc123",
  "program_name": "공정1 PLC 프로그램",
  "description": "공정1 라인용 PLC 프로그램",
  "status": "completed",
  "create_user": "user001",
  "create_dt": "2025-11-13T10:00:00"
}
```

---

### 4. 파일 다운로드
**GET** `/v1/programs/files/download`

**Query Parameters:**
- `file_type` (required): 파일 타입
  - `template`: PGM 등록용 템플릿 (XLSX)
  - `logic_file`: 로직 파일
  - `logic_classification`: Logic 분류체계 (XLSX)
  - `plc_ladder_comment`: PLC Ladder Comment 파일 (CSV)
- `program_id` (optional): Program ID (동적 파일인 경우 필수)

**Response:**
- Binary file with proper headers

---

### 5. 실패한 파일 재시도
**POST** `/v1/programs/{program_id}/retry`

**Path Parameters:**
- `program_id` (required): 프로그램 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID
- `retry_type` (optional): 재시도 타입 (default: "all")
  - `preprocessing`: 전처리 실패 파일만
  - `document`: Document 저장 실패 파일만
  - `all`: 모든 실패 파일

**Response:**
```json
{
  "message": "재시도가 진행되었습니다.",
  "retried_count": 5
}
```

---

### 6. 실패 내역 조회
**GET** `/v1/programs/{program_id}/failures`

**Path Parameters:**
- `program_id` (required): 프로그램 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID
- `failure_type` (optional): 실패 타입 필터

**Response:**
```json
{
  "program_id": "pgm_abc123",
  "failures": [
    {
      "failure_id": "fail_xyz789",
      "failure_type": "preprocessing",
      "filename": "logic001.txt",
      "error_message": "파일 파싱 실패",
      "retry_count": 2,
      "status": "pending"
    }
  ],
  "count": 1
}
```

---

### 7. Knowledge 상태 동기화
**POST** `/v1/programs/{program_id}/knowledge-status/sync`

**Path Parameters:**
- `program_id` (required): 프로그램 ID

**Response:**
```json
{
  "message": "Knowledge 상태가 동기화되었습니다.",
  "updated_count": 10
}
```

---

### 8. Knowledge 상태 조회
**GET** `/v1/programs/{program_id}/knowledge-status`

**Path Parameters:**
- `program_id` (required): 프로그램 ID

**Response:**
```json
{
  "program_id": "pgm_abc123",
  "knowledge_references": [
    {
      "reference_id": "ref_001",
      "reference_type": "plc",
      "name": "PLC 레포지토리",
      "repo_id": "repo_123",
      "documents": [],
      "document_count": 150
    }
  ],
  "total_references": 1
}
```

---

### 9. 프로그램 삭제
**DELETE** `/v1/programs`

**Query Parameters:**
- `program_ids` (required): 삭제할 프로그램 ID 리스트
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "message": "2개의 프로그램이 삭제되었습니다.",
  "deleted_count": 2,
  "failed_count": 0,
  "results": [],
  "errors": [],
  "requested_ids": ["pgm_001", "pgm_002"]
}
```

---

### 10. 매핑용 프로그램 목록
**GET** `/v1/programs/mapping`

**Query Parameters:**
- `program_id` (optional): PGM ID로 검색
- `program_name` (optional): 제목으로 검색
- `page` (optional): 페이지 번호
- `page_size` (optional): 페이지당 항목 수

**Response:**
```json
{
  "items": [
    {
      "program_id": "pgm_abc123",
      "program_name": "공정1 PLC 프로그램",
      "ladder_file_count": 150,
      "comment_file_count": 1,
      "create_user": "user001",
      "create_dt": "2025-11-13T10:00:00"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

## PLC 관리 API

### 1. PLC 정보 조회
**GET** `/v1/plc/{plc_id}`

**Path Parameters:**
- `plc_id` (required): PLC ID (Primary Key)

**Response:**
```json
{
  "id": "plc_001",
  "plc_id": "PLC_A001",
  "plc_name": "PLC 라인 A",
  "plant": {
    "plant_id": "plant_001",
    "plant_code": "P001",
    "plant_name": "공장1"
  },
  "process": {
    "process_id": "process_001",
    "process_code": "PR001",
    "process_name": "공정1"
  },
  "line": {
    "line_id": "line_001",
    "line_code": "L001",
    "line_name": "라인A"
  },
  "equipment_group": {
    "equipment_group_id": "eq_001",
    "equipment_group_code": "EQ001",
    "equipment_group_name": "장비그룹A"
  },
  "unit": "UNIT-01",
  "program_id": "pgm_abc123",
  "program_id_changed": false,
  "previous_program_id": null
}
```

---

### 2. PLC 목록 조회
**GET** `/v1/plc`

**Query Parameters:**
- `plant_id` (optional): Plant ID 필터링
- `process_id` (optional): 공정 ID 필터링
- `line_id` (optional): Line ID 필터링
- `equipment_group_id` (optional): 장비 그룹 ID 필터링
- `plc_id` (optional): PLC ID로 검색
- `plc_name` (optional): PLC 명으로 검색
- `page` (optional): 페이지 번호 (default: 1)
- `page_size` (optional): 페이지당 항목 수 (default: 10, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": "plc_001",
      "plc_id": "PLC_A001",
      "plc_name": "PLC 라인 A",
      "plant_name": "공장1",
      "process_name": "공정1",
      "line_name": "라인A",
      "equipment_group_name": "장비그룹A",
      "unit": "UNIT-01",
      "program_id": "pgm_abc123",
      "program_name": "공정1 PLC 프로그램",
      "mapping_user": "user001",
      "mapping_dt": "2025-11-13T10:00:00"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

### 3. PLC-Program 매핑
**PUT** `/v1/plc/mapping`

**Request Body:**
```json
{
  "plc_ids": ["plc_001", "plc_002"],
  "program_id": "pgm_abc123",
  "mapping_user": "user001"
}
```

**Response:**
```json
{
  "success": true,
  "mapped_count": 2,
  "failed_count": 0,
  "errors": []
}
```

---

### 4. PLC 트리 구조 조회
**GET** `/v1/plc/tree`

**Query Parameters:**
- `is_active` (optional): 활성 PLC만 조회 (기본값: True)

**Response:**
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

**계층 구조:**
- Plant (공장) → Process (공정) → Line (라인) → Equipment Group (장비 그룹) → Unit (호기) → PLC 정보

**사용 예시:**
- 전체 트리: `GET /v1/plc/tree`
- 비활성 포함: `GET /v1/plc/tree?is_active=false`

---

## 개요

### Base URL
```
http://localhost:8000/v1
```

### API 버전
- **현재 버전**: v1
- **프로토콜**: HTTP/HTTPS
- **응답 형식**: JSON
- **인코딩**: UTF-8

### Swagger UI
- **URL**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 인증 및 권한

### 현재 구현 상태
- **인증 방식**: Query Parameter `user_id` 기반
- **향후 계획**: JWT Token 기반 인증 도입

### 권한 체계
- **사용자 레벨**: 개인 문서 및 채팅 접근
- **그룹 레벨**: SIT Auth, NCT Auth, 서비스 권한
- **문서 레벨**: 공개/비공개, 권한 리스트

---

## 공통 응답 형식

### 성공 응답
```json
{
  "status": "success",
  "message": "요청이 성공적으로 처리되었습니다",
  "data": { ... }
}
```

### 에러 응답
```json
{
  "code": -1000,
  "message": "에러 메시지",
  "detail": "상세한 에러 정보"
}
```

---

## 채팅 API

### 1. 채팅방 생성
**POST** `/v1/chat/chats`

**Request Body:**
```json
{
  "chat_title": "새로운 채팅",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "chat_id": "chat_abc123",
  "chat_title": "새로운 채팅",
  "user_id": "user123",
  "created_at": "2025-11-11T10:00:00"
}
```

---

### 2. 채팅방 목록 조회
**GET** `/v1/chat/chats?user_id={user_id}`

**Query Parameters:**
- `user_id` (required): 사용자 ID

**Response:**
```json
{
  "chats": [
    {
      "chat_id": "chat_abc123",
      "chat_title": "새로운 채팅",
      "user_id": "user123",
      "last_message_at": "2025-11-11T10:05:00",
      "is_active": true,
      "reviewer_count": 0
    }
  ]
}
```

---

### 3. 메시지 전송 (Simple)
**POST** `/v1/chat/{chat_id}/message`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Request Body:**
```json
{
  "message": "안녕하세요",
  "user_id": "user123",
  "plc_id": "plc_001"  // optional
}
```

**Response:**
```json
{
  "message_id": "msg_xyz789",
  "content": "안녕하세요! 무엇을 도와드릴까요?",
  "user_id": "ai",
  "timestamp": "2025-11-11T10:05:00"
}
```

---

### 4. 메시지 전송 (Streaming)
**POST** `/v1/chat/{chat_id}/stream`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Request Body:**
```json
{
  "message": "긴 답변이 필요한 질문입니다",
  "user_id": "user123",
  "plc_id": "plc_001"  // optional
}
```

**Response (SSE - Server-Sent Events):**
```
data: {"type":"user_message","message_id":"msg_abc","content":"질문","timestamp":"..."}

data: {"type":"heartbeat","message":"사용자의 의도를 파악하고 있습니다...","timestamp":"..."}

data: {"type":"ai_message_start","message_id":"msg_xyz","timestamp":"..."}

data: {"type":"ai_message_chunk","content":"안녕","delta":"안녕","timestamp":"..."}

data: {"type":"ai_message_chunk","content":"안녕하세요","delta":"하세요","timestamp":"..."}

data: {"type":"ai_message_end","message_id":"msg_xyz","full_content":"안녕하세요!","timestamp":"..."}
```

**Heartbeat 메시지:**
- **10초 경과**: "사용자의 의도를 파악하고 있습니다..."
- **30초 경과**: "정확한 답변을 찾기 위해 노력하고 있습니다..."
- **50초 이후**: "거의 다 완료되었습니다. 조금만 기다려주세요..."

---

### 5. 대화 이력 조회
**GET** `/v1/chat/{chat_id}/history`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Response:**
```json
{
  "history": [
    {
      "message_id": "msg_001",
      "role": "user",
      "content": "안녕하세요",
      "timestamp": "2025-11-11T10:00:00"
    },
    {
      "message_id": "msg_002",
      "role": "assistant",
      "content": "안녕하세요! 무엇을 도와드릴까요?",
      "timestamp": "2025-11-11T10:00:05"
    }
  ]
}
```

---

### 6. 대화 초기화
**POST** `/v1/chat/{chat_id}/clear`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Response:**
```json
{
  "message": "대화 기록이 초기화되었습니다."
}
```

---

### 7. AI 응답 취소
**POST** `/v1/chat/{chat_id}/cancel`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "message": "AI 응답 생성이 취소되었습니다.",
  "cancelled": true
}
```

---

### 8. 채팅방 삭제
**DELETE** `/v1/chat/chats/{chat_id}`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Response:**
```json
{
  "message": "채팅이 삭제되었습니다.",
  "deleted": true
}
```

---

### 9. 채팅방 제목 변경
**PUT** `/v1/chat/chats/{chat_id}/title`

**Path Parameters:**
- `chat_id` (required): 채팅방 ID

**Query Parameters:**
- `new_title` (required): 새 제목
- `user_id` (required): 사용자 ID

**Response:**
```json
{
  "message": "채팅방 이름이 변경되었습니다.",
  "success": true
}
```

---

### 10. 채팅방 제목 자동 생성
**POST** `/v1/chat/generate-title`

**Request Body:**
```json
{
  "message": "파이썬으로 웹 크롤링하는 방법을 알려주세요"
}
```

**Response:**
```json
{
  "title": "파이썬 웹 크롤링 가이드"
}
```

---

## 사용자 API

### 1. 사용자 생성
**POST** `/v1/users`

**Request Body:**
```json
{
  "user_id": "user123",
  "employee_id": "EMP001",
  "name": "홍길동"
}
```

**Response:**
```json
{
  "user_id": "user123",
  "employee_id": "EMP001",
  "name": "홍길동"
}
```

---

### 2. 사용자 조회 (ID)
**GET** `/v1/users/{user_id}`

**Path Parameters:**
- `user_id` (required): 사용자 ID

**Response:**
```json
{
  "user_id": "user123",
  "employee_id": "EMP001",
  "name": "홍길동",
  "site_list": ["SITE_A", "SITE_B"],
  "create_dt": "2025-11-11T09:00:00",
  "is_active": true,
  "is_deleted": false
}
```

---

### 3. 사용자 조회 (사번)
**GET** `/v1/users/employee/{employee_id}`

**Path Parameters:**
- `employee_id` (required): 사번

**Response:**
```json
{
  "user_id": "user123",
  "employee_id": "EMP001",
  "name": "홍길동",
  "site_list": ["SITE_A", "SITE_B"],
  "create_dt": "2025-11-11T09:00:00",
  "is_active": true,
  "is_deleted": false
}
```

---

### 4. 사용자 목록 조회
**GET** `/v1/users`

**Query Parameters:**
- `skip` (optional): 건너뛸 개수 (default: 0)
- `limit` (optional): 조회할 개수 (default: 100, max: 1000)
- `is_active` (optional): 활성 상태 필터

**Response:**
```json
{
  "users": [
    {
      "user_id": "user123",
      "employee_id": "EMP001",
      "name": "홍길동",
      "is_active": true
    }
  ],
  "total_count": 1,
  "skip": 0,
  "limit": 100
}
```

---

### 5. 사용자 검색
**GET** `/v1/users/search`

**Query Parameters:**
- `keyword` (required): 검색 키워드 (이름 또는 사번)
- `skip` (optional): 건너뛸 개수 (default: 0)
- `limit` (optional): 조회할 개수 (default: 100)

**Response:**
```json
{
  "users": [
    {
      "user_id": "user123",
      "employee_id": "EMP001",
      "name": "홍길동"
    }
  ],
  "keyword": "홍길동",
  "total_count": 1,
  "skip": 0,
  "limit": 100
}
```

---

### 6. 사용자 수정
**PUT** `/v1/users/{user_id}`

**Path Parameters:**
- `user_id` (required): 사용자 ID

**Request Body:**
```json
{
  "name": "홍길동2",
  "employee_id": "EMP002"
}
```

**Response:**
```json
{
  "user_id": "user123"
}
```

---

### 7. 사용자 비활성화
**PATCH** `/v1/users/{user_id}/deactivate`

**Path Parameters:**
- `user_id` (required): 사용자 ID

**Response:**
```json
{
  "user_id": "user123",
  "is_active": false,
  "message": "사용자가 비활성화되었습니다."
}
```

---

### 8. 사용자 활성화
**PATCH** `/v1/users/{user_id}/activate`

**Path Parameters:**
- `user_id` (required): 사용자 ID

**Response:**
```json
{
  "user_id": "user123",
  "is_active": true,
  "message": "사용자가 활성화되었습니다."
}
```

---

### 9. 사용자 삭제
**DELETE** `/v1/users/{user_id}`

**Path Parameters:**
- `user_id` (required): 사용자 ID

**Response:**
```json
{
  "user_id": "user123"
}
```

---

### 10. 사용자 통계
**GET** `/v1/users/stats/count`

**Query Parameters:**
- `is_active` (optional): 활성 상태 필터

**Response:**
```json
{
  "total_count": 100,
  "active_count": 80,
  "inactive_count": 20
}
```

---

### 11. 사용자 존재 확인
**GET** `/v1/users/check/exists`

**Query Parameters:**
- `user_id` (optional): 사용자 ID
- `employee_id` (optional): 사번
- *둘 중 하나는 필수*

**Response:**
```json
{
  "exists": true,
  "user_id": "user123",
  "employee_id": "EMP001"
}
```

---

## 문서 관리 API

### 1. 문서 업로드
**POST** `/v1/upload`

**Request (multipart/form-data):**
- `file` (required): 업로드 파일
- `user_id` (optional): 사용자 ID (default: "user")
- `is_public` (optional): 공개 여부 (default: false)
- `permissions` (optional): 권한 리스트 (JSON 문자열)
- `document_type` (optional): 문서 타입 (default: "common")

**Response:**
```json
{
  "status": "success",
  "message": "문서가 업로드되었습니다.",
  "data": {
    "document_id": "doc_abc123",
    "document_name": "report.pdf",
    "file_size": 1048576,
    "upload_path": "/uploads/user/report.pdf",
    "status": "processing"
  }
}
```

---

### 2. 폴더 업로드
**POST** `/v1/upload-folder`

**Request (form-data):**
- `folder_path` (required): 폴더 경로
- `user_id` (optional): 사용자 ID (default: "user")
- `is_public` (optional): 공개 여부 (default: false)

**Response:**
```json
{
  "status": "success",
  "message": "폴더 업로드 완료: 10개 성공, 0개 실패",
  "uploaded_count": 10,
  "failed_count": 0,
  "failed_files": [],
  "uploaded_documents": [...]
}
```

---

### 3. 문서 목록 조회
**GET** `/v1/documents`

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "document_id": "doc_abc123",
      "document_name": "report.pdf",
      "file_size": 1048576,
      "file_type": "application/pdf",
      "status": "completed",
      "create_dt": "2025-11-11T10:00:00"
    }
  ]
}
```

---

### 4. 문서 상세 조회
**GET** `/v1/documents/{document_id}`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "data": {
    "document_id": "doc_abc123",
    "document_name": "report.pdf",
    "original_filename": "report.pdf",
    "file_size": 1048576,
    "file_type": "application/pdf",
    "status": "completed",
    "total_pages": 10,
    "processed_pages": 10,
    "vector_count": 50,
    "milvus_collection_name": "collection_001",
    "permissions": ["SITE_A", "SITE_B"]
  }
}
```

---

### 5. 문서 다운로드
**GET** `/v1/documents/{document_id}/download`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
- Binary file with proper headers
- `Content-Disposition: attachment; filename*=UTF-8''...`

---

### 6. 문서 뷰어
**GET** `/v1/documents/{document_id}/view`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
- Binary file with inline display
- `Content-Disposition: inline`

---

### 7. 문서 검색
**GET** `/v1/search`

**Query Parameters:**
- `search_term` (required): 검색어
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "document_id": "doc_abc123",
      "document_name": "report.pdf",
      "file_size": 1048576
    }
  ]
}
```

---

### 8. 문서 삭제
**DELETE** `/v1/documents/{document_id}`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "message": "문서가 삭제되었습니다."
}
```

---

### 9. 문서 통계 조회
**GET** `/v1/stats`

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_documents": 100,
    "total_size": 104857600,
    "file_type_stats": {
      "application/pdf": {
        "count": 50,
        "total_size": 52428800
      },
      "image/jpeg": {
        "count": 30,
        "total_size": 31457280
      }
    }
  }
}
```

---

### 10. 문서 처리 통계
**GET** `/v1/processing-stats`

**Query Parameters:**
- `user_id` (optional): 사용자 ID (default: "user")

**Response:**
```json
{
  "status": "success",
  "data": {
    "status_counts": {
      "completed": 80,
      "processing": 15,
      "failed": 5
    },
    "total_pages": 1000,
    "total_vectors": 5000,
    "avg_pages_per_doc": 10.0,
    "avg_vectors_per_doc": 50.0
  }
}
```

---

### 11. 문서 처리 상태 업데이트
**PUT** `/v1/documents/{document_id}/processing`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Request (form-data):**
- `status` (required): 처리 상태
- `user_id` (optional): 사용자 ID
- `total_pages` (optional): 전체 페이지
- `processed_pages` (optional): 처리된 페이지
- `vector_count` (optional): 벡터 개수
- `milvus_collection_name` (optional): Milvus 컬렉션명

**Response:**
```json
{
  "status": "success",
  "message": "문서 처리 정보가 업데이트되었습니다."
}
```

---

### 12. 문서 권한 조회
**GET** `/v1/documents/{document_id}/permissions`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Query Parameters:**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "document_id": "doc_abc123",
    "permissions": ["SITE_A", "SITE_B", "ADMIN"]
  }
}
```

---

### 13. 문서 권한 업데이트
**PUT** `/v1/documents/{document_id}/permissions`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Request (form-data):**
- `user_id` (optional): 사용자 ID
- `permissions` (required): 권한 리스트 (JSON 문자열)

**Response:**
```json
{
  "status": "success",
  "message": "문서 권한이 업데이트되었습니다."
}
```

---

### 14. 문서 권한 추가
**POST** `/v1/documents/{document_id}/permissions/{permission}`

**Path Parameters:**
- `document_id` (required): 문서 ID
- `permission` (required): 추가할 권한

**Request (form-data):**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "status": "success",
  "message": "'SITE_C' 권한이 추가되었습니다."
}
```

---

### 15. 문서 권한 제거
**DELETE** `/v1/documents/{document_id}/permissions/{permission}`

**Path Parameters:**
- `document_id` (required): 문서 ID
- `permission` (required): 제거할 권한

**Query Parameters:**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "status": "success",
  "message": "'SITE_C' 권한이 제거되었습니다."
}
```

---

### 16. 특정 권한을 가진 문서 조회
**GET** `/v1/documents/permissions/{permission}`

**Path Parameters:**
- `permission` (required): 권한

**Query Parameters:**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "document_id": "doc_abc123",
      "document_name": "report.pdf"
    }
  ]
}
```

---

### 17. 문서 타입별 조회
**GET** `/v1/documents/types/{document_type}`

**Path Parameters:**
- `document_type` (required): 문서 타입 (common/type1/type2)

**Query Parameters:**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "document_id": "doc_abc123",
      "document_name": "report.pdf",
      "document_type": "common"
    }
  ]
}
```

---

### 18. 문서 타입 업데이트
**PUT** `/v1/documents/{document_id}/type`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Request (form-data):**
- `user_id` (optional): 사용자 ID
- `document_type` (required): 문서 타입

**Response:**
```json
{
  "status": "success",
  "message": "문서 타입이 'type1'으로 업데이트되었습니다."
}
```

---

### 19. 문서 타입별 통계
**GET** `/v1/document-type-stats`

**Query Parameters:**
- `user_id` (optional): 사용자 ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "type_statistics": {
      "common": 80,
      "type1": 15,
      "type2": 5
    },
    "total_documents": 100,
    "available_types": ["common", "type1", "type2"]
  }
}
```

---

### 20. 문서 처리 작업 조회
**GET** `/v1/processing-jobs/{document_id}`

**Path Parameters:**
- `document_id` (required): 문서 ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "document_id": "doc_abc123",
    "processing_jobs": [
      {
        "job_id": "job_xyz789",
        "job_type": "embedding",
        "status": "completed",
        "started_at": "2025-11-11T10:00:00",
        "completed_at": "2025-11-11T10:05:00"
      }
    ],
    "total_jobs": 1
  }
}
```

---

### 21. 처리 진행률 조회
**GET** `/v1/processing-progress/{job_id}`

**Path Parameters:**
- `job_id` (required): 작업 ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "job_id": "job_xyz789",
    "progress_percent": 75.0,
    "current_step": "임베딩 생성 중",
    "completed_steps": 3,
    "total_steps": 4,
    "job_status": "running"
  }
}
```

---

## 에러 코드

### HTTP 상태 코드
- `200`: 성공
- `400`: 잘못된 요청
- `401`: 인증 실패
- `403`: 권한 없음
- `404`: 리소스 없음
- `500`: 서버 에러

### 커스텀 에러 코드
| 코드 | 메시지 | 설명 |
|------|--------|------|
| -1 | 사용자를 찾을 수 없습니다 | 사용자 ID가 존재하지 않음 |
| -2 | 정의되지 않은 오류입니다 | 예상하지 못한 에러 |
| -1000 | 채팅을 찾을 수 없습니다 | 채팅방 ID가 존재하지 않음 |
| -1001 | 채팅 메시지 저장 실패 | 메시지 저장 중 에러 |
| -2000 | 문서를 찾을 수 없습니다 | 문서 ID가 존재하지 않음 |
| -2001 | 문서 접근 권한이 없습니다 | 권한 부족 |
| -2002 | 파일 업로드 실패 | 파일 저장 중 에러 |

---

## 예제 코드

### Python (requests)
```python
import requests

# 채팅방 생성
response = requests.post(
    "http://localhost:8000/v1/chat/chats",
    json={
        "chat_title": "새로운 채팅",
        "user_id": "user123"
    }
)
chat_id = response.json()["chat_id"]

# 메시지 전송 (스트리밍)
response = requests.post(
    f"http://localhost:8000/v1/chat/{chat_id}/stream",
    json={
        "message": "안녕하세요",
        "user_id": "user123"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = line.decode('utf-8')
        if data.startswith('data: '):
            print(data[6:])
```

### JavaScript (fetch)
```javascript
// 채팅방 생성
const response = await fetch('http://localhost:8000/v1/chat/chats', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    chat_title: '새로운 채팅',
    user_id: 'user123'
  })
});
const { chat_id } = await response.json();

// 메시지 전송 (스트리밍)
const streamResponse = await fetch(
  `http://localhost:8000/v1/chat/${chat_id}/stream`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: '안녕하세요',
      user_id: 'user123'
    })
  }
);

const reader = streamResponse.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const text = decoder.decode(value);
  const lines = text.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));
      console.log(data);
    }
  }
}
```

### cURL
```bash
# 채팅방 생성
curl -X POST http://localhost:8000/v1/chat/chats \
  -H "Content-Type: application/json" \
  -d '{"chat_title":"새로운 채팅","user_id":"user123"}'

# 메시지 전송 (Simple)
curl -X POST http://localhost:8000/v1/chat/{chat_id}/message \
  -H "Content-Type: application/json" \
  -d '{"message":"안녕하세요","user_id":"user123"}'

# 문서 업로드
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@/path/to/file.pdf" \
  -F "user_id=user123" \
  -F "is_public=false"
```

---

## 변경 이력

### v1.2.0 (2025-11-13)
- PLC 트리 구조 조회 API 추가 (`GET /v1/plc/tree`)
- 계층적 트리 형식으로 PLC 데이터 제공
- SQL JOIN 최적화로 성능 향상

### v1.1.0 (2025-11-13)
- Program 관리 API 추가 (10개 엔드포인트)
- PLC 관리 API 추가 (4개 엔드포인트)
- Knowledge 상태 관리 API 추가
- S3 파일 다운로드 API 추가
- 프로그램 등록 및 실패 처리 API 추가

### v1.0.0 (2025-11-11)
- 초기 API 버전
- 채팅, 사용자, 문서 관리 API 구현
- SSE 기반 스트리밍 지원
- 권한 관리 시스템 도입

---

**최종 업데이트**: 2025-11-13
**문서 버전**: 1.1.0
