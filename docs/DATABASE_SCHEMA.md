# 📊 데이터베이스 스키마 문서

## 목차
- [개요](#개요)
- [ERD](#erd)
- [테이블 상세](#테이블-상세)
- [관계 및 제약조건](#관계-및-제약조건)
- [인덱스 전략](#인덱스-전략)

---

## 개요

### 데이터베이스 정보
- **DBMS**: PostgreSQL 12+
- **ORM**: SQLAlchemy 1.4+
- **스키마**: public
- **인코딩**: UTF-8

### 테이블 분류

#### 1. 사용자 및 권한 (User & Permission)
- `USERS` - 사용자 정보
- `GROUPS` - 그룹 및 권한 정보

#### 2. 채팅 서비스 (Chat Service)
- `CHATS` - 채팅방 정보
- `CHAT_MESSAGES` - 채팅 메시지
- `MESSAGE_RATINGS` - 메시지 평가

#### 3. 문서 관리 (Document Management)
- `DOCUMENTS` - 문서 메타데이터
- `DOCUMENT_CHUNKS` - 문서 청크 (벡터 검색용)
- `PROCESSING_JOBS` - 문서 처리 작업

#### 4. 프로그램 관리 (Program Management)
- `PROGRAMS` - 프로그램 정보
- `PROCESSING_FAILURES` - 처리 실패 로그
- `PROGRAM_LLM_DATA_CHUNKS` - 프로그램 LLM 데이터

#### 5. PLC 및 기준정보 (PLC & Master Data)
- `PLC` - PLC 정보 및 프로그램 매핑
- `PLANT_MASTER` - 공장 기준정보
- `PROCESS_MASTER` - 공정 기준정보
- `LINE_MASTER` - 라인 기준정보
- `EQUIPMENT_GROUP_MASTER` - 장비 그룹 기준정보

#### 6. 템플릿 및 지식베이스 (Template & Knowledge)
- `TEMPLATES` - 템플릿 정보
- `TEMPLATE_DATA` - 템플릿 데이터
- `KNOWLEDGE_REFERENCES` - Knowledge Base 참조

---

## ERD

### 전체 ERD (간소화)

```
┌─────────────┐        ┌──────────────┐        ┌─────────────────┐
│   USERS     │───────▶│    CHATS     │───────▶│ CHAT_MESSAGES   │
│             │        │              │        │                 │
│ user_id (PK)│        │ chat_id (PK) │        │ message_id (PK) │
│ employee_id │        │ user_id (FK) │        │ chat_id (FK)    │
│ name        │        │ chat_title   │        │ message         │
│ site_list   │        │              │        │ plc_id (FK)     │
└─────────────┘        └──────────────┘        └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │MESSAGE_RATINGS  │
                                               │                 │
                                               │ rating_id (PK)  │
                                               │ message_id (FK) │
                                               │ rating_score    │
                                               └─────────────────┘

┌──────────────┐        ┌─────────────────┐        ┌──────────────────┐
│   PROGRAMS   │◀──────▶│   DOCUMENTS     │───────▶│ DOCUMENT_CHUNKS  │
│              │        │                 │        │                  │
│ program_id PK│        │ document_id (PK)│        │ chunk_id (PK)    │
│ program_name │        │ program_id (FK) │        │ doc_id (FK)      │
│ status       │        │ user_id         │        │ page_number      │
└──────────────┘        │ status          │        │ content          │
       │                │ milvus_...      │        │ milvus_id        │
       │                └─────────────────┘        └──────────────────┘
       │
       ▼
┌──────────────────┐    ┌─────────────────┐
│PROCESSING_FAILURES│    │PROCESSING_JOBS  │
│                  │    │                 │
│ failure_id (PK)  │    │ job_id (PK)     │
│ program_id (FK)  │    │ doc_id          │
│ failure_type     │    │ program_id (FK) │
│ retry_count      │    │ status          │
└──────────────────┘    └─────────────────┘

┌──────────┐    ┌─────────────────┐    ┌──────────────┐    ┌────────────┐
│  PLANT   │◀───│    PROCESS      │◀───│     LINE     │◀───│EQUIP_GROUP │
│  MASTER  │    │    MASTER       │    │    MASTER    │    │  MASTER    │
│          │    │                 │    │              │    │            │
│plant_id  │    │process_id (PK)  │    │line_id (PK)  │    │equip_grp_id│
│plant_code│    │plant_id (FK)    │    │process_id FK │    │line_id (FK)│
└──────────┘    └─────────────────┘    └──────────────┘    └────────────┘
                                                │
                                                ▼
                                           ┌─────────┐
                                           │   PLC   │
                                           │         │
                                           │ id (PK) │
                                           │ plc_id  │
                                           │program FK│
                                           └─────────┘

┌──────────────┐        ┌──────────────────┐
│  TEMPLATES   │───────▶│  TEMPLATE_DATA   │
│              │        │                  │
│template_id PK│        │template_data_id  │
│document_id FK│        │template_id (FK)  │
│program_id FK │        │logic_id          │
└──────────────┘        │document_id (FK)  │
                        └──────────────────┘

┌──────────────────────┐
│ KNOWLEDGE_REFERENCES │
│                      │
│ reference_id (PK)    │
│ reference_type       │
│ repo_id              │
│ datasource_id        │
└──────────────────────┘
```

---

## 테이블 상세

### 1. USERS (사용자)

**목적**: 시스템 사용자 정보 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| USER_ID | String(50) | PK | 사용자 고유 ID |
| EMPLOYEE_ID | String(20) | NOT NULL, UNIQUE | 사번 |
| NAME | String(100) | NOT NULL | 이름 |
| SITE_LIST | JSON | NULL | 사이트 리스트 (권한) |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| UPDATE_DT | DateTime | NULL | 수정일시 |
| IS_ACTIVE | Boolean | NOT NULL, default=true | 활성 상태 |
| IS_DELETED | Boolean | NOT NULL, default=false | 삭제 여부 |

**인덱스**:
- PK: USER_ID
- UNIQUE: EMPLOYEE_ID

**용도**: 
- 사용자 인증 및 권한 관리
- 문서/채팅 소유권 확인

---

### 2. GROUPS (그룹)

**목적**: 그룹 및 권한 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| GROUP_ID | String(50) | PK | 그룹 고유 ID |
| GROUP_NAME | String(100) | NOT NULL | 그룹명 |
| DESCRIPTION | Text | NULL | 그룹 설명 |
| SIT_AUTH | JSON | default=[] | sitAuth 권한 리스트 |
| NCT_AUTH | String(1) | default='N' | nct 권한 (Y/N) |
| SERVICE_PERMISSIONS | JSON | default=[] | 서비스 권한 리스트 |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| UPDATE_DT | DateTime | NULL | 수정일시 |
| IS_ACTIVE | Boolean | NOT NULL, default=true | 활성 상태 |
| IS_DELETED | Boolean | NOT NULL, default=false | 삭제 여부 |

**인덱스**:
- PK: GROUP_ID

**용도**:
- 그룹별 권한 관리
- 서비스별 접근 제어

---

### 3. CHATS (채팅방)

**목적**: 채팅방 정보 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| CHAT_ID | String(50) | PK | 채팅방 고유 ID |
| CHAT_TITLE | String(100) | NOT NULL | 채팅방 제목 |
| USER_ID | String(50) | NOT NULL | 사용자 ID |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| LAST_MESSAGE_AT | DateTime | NULL | 마지막 메시지 시간 |
| IS_ACTIVE | Boolean | NOT NULL, default=true | 활성 상태 |
| REVIEWER_COUNT | Integer | default=0 | 리뷰어 수 |

**인덱스**:
- PK: CHAT_ID
- INDEX: USER_ID (사용자별 채팅방 조회)

**용도**:
- 채팅방 생성 및 관리
- 사용자별 채팅방 목록 조회

---

### 4. CHAT_MESSAGES (채팅 메시지)

**목적**: 채팅 메시지 저장

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| MESSAGE_ID | String(50) | PK | 메시지 고유 ID |
| CHAT_ID | String(50) | FK, NOT NULL | 채팅방 ID |
| USER_ID | String(50) | NOT NULL | 사용자 ID |
| MESSAGE | Text | NOT NULL | 메시지 내용 |
| MESSAGE_TYPE | String(20) | NOT NULL | 메시지 타입 (user/assistant) |
| STATUS | String(20) | NULL | 상태 (generating/completed/error) |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| IS_DELETED | Boolean | NOT NULL, default=false | 삭제 여부 |
| IS_CANCELLED | Boolean | NOT NULL, default=false | 취소 여부 |
| PLC_ID | String(50) | FK, NULL | PLC 정보 참조 |
| EXTERNAL_API_NODES | JSON | NULL | External API 처리 결과 |

**인덱스**:
- PK: MESSAGE_ID
- FK: CHAT_ID → CHATS.CHAT_ID
- FK: PLC_ID → PLC.ID
- INDEX: CHAT_ID, CREATE_DT (채팅방별 메시지 조회)

**용도**:
- 채팅 메시지 저장
- 대화 이력 관리
- PLC 정보 연결

---

### 5. MESSAGE_RATINGS (메시지 평가)

**목적**: AI 답변 품질 평가

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| RATING_ID | String(50) | PK | 평가 고유 ID |
| MESSAGE_ID | String(50) | FK, UNIQUE, NOT NULL | 메시지 ID |
| USER_ID | String(50) | NOT NULL | 평가자 ID |
| RATING_SCORE | Integer | NOT NULL | 평가 점수 (1-5) |
| RATING_COMMENT | Text | NULL | 평가 코멘트 |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| UPDATED_AT | DateTime | NULL, onupdate=now() | 수정일시 |
| IS_DELETED | Boolean | NOT NULL, default=false | 삭제 여부 |

**인덱스**:
- PK: RATING_ID
- FK: MESSAGE_ID → CHAT_MESSAGES.MESSAGE_ID
- UNIQUE: MESSAGE_ID (메시지당 1개 평가)

**용도**:
- AI 응답 품질 평가
- 평가 통계 수집
- 모델 개선 피드백

---

### 6. DOCUMENTS (문서)

**목적**: 문서 메타데이터 및 처리 상태 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| DOCUMENT_ID | String(50) | PK | 문서 고유 ID |
| DOCUMENT_NAME | String(255) | NOT NULL | 문서명 |
| ORIGINAL_FILENAME | String(255) | NOT NULL | 원본 파일명 |
| FILE_KEY | String(255) | NOT NULL | 파일 키 (경로) |
| FILE_SIZE | Integer | NOT NULL | 파일 크기 (bytes) |
| FILE_TYPE | String(100) | NOT NULL | MIME 타입 |
| FILE_EXTENSION | String(10) | NOT NULL | 파일 확장자 |
| UPLOAD_PATH | String(500) | NOT NULL | 업로드 경로 |
| FILE_HASH | String(64) | NULL | 파일 해시 (중복 방지) |
| USER_ID | String(50) | NOT NULL | 업로드 사용자 |
| IS_PUBLIC | Boolean | NOT NULL, default=false | 공개 여부 |
| DOCUMENT_TYPE | String(20) | NULL, default='common' | 문서 타입 |
| STATUS | String(20) | NOT NULL, default='processing' | 처리 상태 |
| TOTAL_PAGES | Integer | default=0 | 전체 페이지 수 |
| PROCESSED_PAGES | Integer | default=0 | 처리된 페이지 수 |
| ERROR_MESSAGE | Text | NULL | 에러 메시지 |
| MILVUS_COLLECTION_NAME | String(255) | NULL | Milvus 컬렉션명 |
| VECTOR_COUNT | Integer | default=0 | 벡터 개수 |
| LANGUAGE | String(10) | NULL | 문서 언어 |
| AUTHOR | String(255) | NULL | 작성자 |
| SUBJECT | String(500) | NULL | 주제 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| PROCESSING_CONFIG | JSON | NULL | 처리 설정 |
| PERMISSIONS | JSON | NULL | 권한 리스트 |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| UPDATED_AT | DateTime | NULL, onupdate=now() | 수정일시 |
| PROCESSED_AT | DateTime | NULL | 처리 완료 시간 |
| IS_DELETED | Boolean | NOT NULL, default=false | 삭제 여부 |
| PROGRAM_ID | String(50) | FK, NULL | 프로그램 ID |
| PROGRAM_FILE_TYPE | String(50) | NULL | 프로그램 파일 타입 |
| SOURCE_DOCUMENT_ID | String(50) | FK, NULL | 원본 문서 ID |
| KNOWLEDGE_REFERENCE_ID | String(50) | FK, NULL | Knowledge Base 참조 |

**인덱스**:
- PK: DOCUMENT_ID
- FK: PROGRAM_ID → PROGRAMS.PROGRAM_ID
- FK: SOURCE_DOCUMENT_ID → DOCUMENTS.DOCUMENT_ID
- FK: KNOWLEDGE_REFERENCE_ID → KNOWLEDGE_REFERENCES.REFERENCE_ID
- INDEX: USER_ID, STATUS, DOCUMENT_TYPE, PROGRAM_ID

**용도**:
- 파일 업로드 관리
- 문서 처리 상태 추적
- 벡터 검색 메타데이터
- 권한 관리

---

### 7. DOCUMENT_CHUNKS (문서 청크)

**목적**: 문서 벡터 검색용 청크 저장

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| ID | UUID | PK | 청크 고유 ID |
| CHUNK_ID | String(255) | UNIQUE, NOT NULL | 청크 ID |
| DOC_ID | String(255) | NOT NULL | 문서 ID (DOCUMENTS.DOCUMENT_ID) |
| PAGE_NUMBER | Integer | NOT NULL | 페이지 번호 |
| CHUNK_TYPE | String(50) | NOT NULL | 청크 타입 (text/image/combined) |
| CONTENT | Text | NULL | 텍스트 내용 |
| IMAGE_DESCRIPTION | Text | NULL | 이미지 설명 (GPT-4 Vision) |
| IMAGE_PATH | String(500) | NULL | 이미지 파일 경로 |
| MILVUS_ID | String(255) | NULL | Milvus 벡터 ID |
| EMBEDDING_MODEL | String(100) | NULL | 임베딩 모델명 |
| VECTOR_DIMENSION | Integer | NULL | 벡터 차원 |
| CHAR_COUNT | Integer | NULL | 문자 수 |
| WORD_COUNT | Integer | NULL | 단어 수 |
| LANGUAGE | String(10) | NULL | 언어 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATED_AT | DateTime | default=now() | 생성일시 |
| UPDATED_AT | DateTime | onupdate=now() | 수정일시 |

**인덱스**:
- PK: ID
- UNIQUE: CHUNK_ID
- INDEX: DOC_ID, PAGE_NUMBER, CHUNK_TYPE

**용도**:
- 벡터 검색용 청크 관리
- 페이지별 내용 추적
- 이미지 설명 저장

---

### 8. PROCESSING_JOBS (처리 작업)

**목적**: 문서 처리 작업 로그

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| ID | UUID | PK | 작업 고유 ID |
| JOB_ID | String(255) | UNIQUE, NOT NULL | 작업 ID |
| DOC_ID | String(255) | NOT NULL | 문서 ID |
| JOB_TYPE | String(50) | NOT NULL | 작업 타입 (embedding/processing) |
| STATUS | String(20) | NOT NULL, default='running' | 상태 (running/completed/failed) |
| FLOW_RUN_ID | String(255) | NULL | Prefect Flow Run ID |
| TOTAL_STEPS | Integer | default=0 | 전체 단계 수 |
| COMPLETED_STEPS | Integer | default=0 | 완료 단계 수 |
| CURRENT_STEP | String(255) | NULL | 현재 단계 |
| RESULT_DATA | JSON | NULL | 결과 데이터 |
| ERROR_MESSAGE | Text | NULL | 에러 메시지 |
| PROGRAM_ID | String(50) | FK, NULL | 프로그램 ID |
| STARTED_AT | DateTime | default=now() | 시작 시간 |
| COMPLETED_AT | DateTime | NULL | 완료 시간 |
| UPDATED_AT | DateTime | onupdate=now() | 수정 시간 |

**인덱스**:
- PK: ID
- UNIQUE: JOB_ID
- FK: PROGRAM_ID → PROGRAMS.PROGRAM_ID
- INDEX: DOC_ID, STATUS, JOB_TYPE

**용도**:
- 처리 작업 추적
- Prefect 워크플로우 연동
- 실패 분석

---

### 9. PROGRAMS (프로그램)

**목적**: PLC 프로그램 정보 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| PROGRAM_ID | String(50) | PK | 프로그램 고유 ID |
| PROGRAM_NAME | String(255) | NOT NULL | 프로그램명 |
| DESCRIPTION | Text | NULL | 설명 |
| STATUS | String(50) | NOT NULL, default='preparing' | 상태 |
| ERROR_MESSAGE | Text | NULL | 에러 메시지 |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| CREATE_USER | String(50) | NOT NULL | 생성자 |
| UPDATE_DT | DateTime | NULL, onupdate=now() | 수정일시 |
| UPDATE_USER | String(50) | NULL | 수정자 |
| COMPLETED_AT | DateTime | NULL | 완료 시간 |
| IS_USED | Boolean | NOT NULL, default=true | 사용 여부 |

**상태값**:
- `preparing` - 준비 중
- `uploading` - 업로드 중
- `processing` - 처리 중
- `embedding` - 임베딩 중
- `completed` - 완료
- `failed` - 실패

**인덱스**:
- PK: PROGRAM_ID
- INDEX: STATUS, CREATE_USER

**용도**:
- PLC 프로그램 업로드 관리
- 프로그램 처리 상태 추적

---

### 10. PROCESSING_FAILURES (처리 실패)

**목적**: 처리 실패 정보 및 재시도 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| FAILURE_ID | String(50) | PK | 실패 ID |
| PROGRAM_ID | String(50) | FK, NOT NULL | 프로그램 ID |
| FAILURE_TYPE | String(50) | NOT NULL | 실패 타입 |
| FILE_PATH | String(500) | NULL | 파일 경로 |
| FILE_INDEX | Integer | NULL | 파일 인덱스 |
| FILENAME | String(255) | NULL | 파일명 |
| S3_PATH | String(500) | NULL | S3 경로 |
| S3_KEY | String(500) | NULL | S3 키 |
| ERROR_MESSAGE | Text | NOT NULL | 에러 메시지 |
| ERROR_DETAILS | JSON | NULL | 에러 상세 |
| RETRY_COUNT | Integer | NOT NULL, default=0 | 재시도 횟수 |
| MAX_RETRY_COUNT | Integer | NOT NULL, default=3 | 최대 재시도 |
| STATUS | String(50) | NOT NULL, default='pending' | 상태 |
| RESOLVED_AT | DateTime | NULL | 해결 시간 |
| LAST_RETRY_AT | DateTime | NULL | 마지막 재시도 |
| RESOLVED_BY | String(50) | NULL | 해결자 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATED_AT | DateTime | NOT NULL, default=now() | 생성일시 |
| UPDATED_AT | DateTime | NULL, onupdate=now() | 수정일시 |

**실패 타입**:
- `preprocessing` - 전처리 실패
- `document_storage` - 문서 저장 실패
- `vector_indexing` - 벡터 인덱싱 실패

**상태값**:
- `pending` - 대기 중
- `retrying` - 재시도 중
- `resolved` - 해결됨
- `failed` - 실패

**인덱스**:
- PK: FAILURE_ID
- FK: PROGRAM_ID → PROGRAMS.PROGRAM_ID
- INDEX: PROGRAM_ID, FAILURE_TYPE, STATUS

**용도**:
- 실패 추적 및 분석
- 자동 재시도 관리
- 수동 재처리 지원

---

### 11. PLC (PLC 정보)

**목적**: PLC 기준 정보 및 프로그램 매핑

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| ID | String(50) | PK | PLC 고유 ID |
| PLC_ID | String(50) | NOT NULL | PLC 식별자 (중복 가능) |
| PLC_NAME | String(255) | NOT NULL | PLC 이름 |
| UNIT | String(100) | NULL | 단위 |
| PROGRAM_ID | String(50) | FK, UNIQUE, NULL | 프로그램 ID (1:1) |
| MAPPING_DT | DateTime | NULL | 매핑 시간 |
| MAPPING_USER | String(50) | NULL | 매핑 사용자 |
| IS_ACTIVE | Boolean | NOT NULL, default=true | 활성 상태 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATE_DT | DateTime | NOT NULL, default=now() | 생성일시 |
| CREATE_USER | String(50) | NOT NULL | 생성자 |
| UPDATE_DT | DateTime | NULL, onupdate=now() | 수정일시 |
| UPDATE_USER | String(50) | NULL | 수정자 |

**스냅샷 필드 (불변)**:
- PLANT_ID_SNAPSHOT, PLANT_CODE_SNAPSHOT, PLANT_NAME_SNAPSHOT
- PROCESS_ID_SNAPSHOT, PROCESS_CODE_SNAPSHOT, PROCESS_NAME_SNAPSHOT
- LINE_ID_SNAPSHOT, LINE_CODE_SNAPSHOT, LINE_NAME_SNAPSHOT
- EQUIPMENT_GROUP_ID_SNAPSHOT, EQUIPMENT_GROUP_CODE_SNAPSHOT, EQUIPMENT_GROUP_NAME_SNAPSHOT

**현재 참조 필드 (FK)**:
- PLANT_ID_CURRENT → PLANT_MASTER.PLANT_ID
- PROCESS_ID_CURRENT → PROCESS_MASTER.PROCESS_ID
- LINE_ID_CURRENT → LINE_MASTER.LINE_ID
- EQUIPMENT_GROUP_ID_CURRENT → EQUIPMENT_GROUP_MASTER.EQUIPMENT_GROUP_ID

**인덱스**:
- PK: ID
- FK: PROGRAM_ID → PROGRAMS.PROGRAM_ID (UNIQUE)
- INDEX: PLC_ID, PLANT_ID_CURRENT, PROCESS_ID_CURRENT

**용도**:
- PLC와 프로그램 1:1 매핑
- 기준정보 스냅샷 보관
- 계층적 기준정보 관리

---

### 12-15. Master Data (기준정보)

#### PLANT_MASTER (공장)
- PLANT_ID (PK), PLANT_CODE (UNIQUE), PLANT_NAME
- DISPLAY_ORDER, IS_ACTIVE

#### PROCESS_MASTER (공정)
- PROCESS_ID (PK), PROCESS_CODE (UNIQUE), PROCESS_NAME
- PLANT_ID (FK → PLANT_MASTER)
- DISPLAY_ORDER, IS_ACTIVE

#### LINE_MASTER (라인)
- LINE_ID (PK), LINE_CODE (UNIQUE), LINE_NAME
- PROCESS_ID (FK → PROCESS_MASTER)
- DISPLAY_ORDER, IS_ACTIVE

#### EQUIPMENT_GROUP_MASTER (장비 그룹)
- EQUIPMENT_GROUP_ID (PK), EQUIPMENT_GROUP_CODE (UNIQUE), EQUIPMENT_GROUP_NAME
- LINE_ID (FK → LINE_MASTER)
- DISPLAY_ORDER, IS_ACTIVE

**공통 필드**:
- DESCRIPTION, METADATA_JSON
- CREATE_DT, CREATE_USER, UPDATE_DT, UPDATE_USER

**인덱스**:
- PK: *_ID
- UNIQUE: *_CODE
- FK: 상위 계층 ID

**용도**:
- 계층적 기준정보 관리 (Plant → Process → Line → Equipment Group)
- PLC 매핑 기준
- 표시 순서 및 활성화 관리

---

### 16. PROGRAM_LLM_DATA_CHUNKS (프로그램 LLM 데이터)

**목적**: 프로그램 LLM 학습 데이터 청크 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| CHUNK_ID | String(50) | PK | 청크 ID |
| PROGRAM_ID | String(50) | FK, NOT NULL | 프로그램 ID |
| DATA_TYPE | String(50) | NOT NULL | 데이터 타입 |
| DATA_VERSION | String(50) | NULL | 데이터 버전 |
| CHUNK_INDEX | Integer | NOT NULL | 청크 인덱스 |
| TOTAL_CHUNKS | Integer | NOT NULL | 전체 청크 수 |
| CHUNK_SIZE | Integer | NOT NULL | 청크 크기 |
| TOTAL_SIZE | Integer | NULL | 전체 크기 |
| S3_BUCKET | String(255) | NULL | S3 버킷 |
| S3_KEY | String(500) | NOT NULL | S3 키 |
| S3_URL | String(1000) | NULL | S3 URL |
| FILE_HASH | String(64) | NULL | 파일 해시 |
| CHECKSUM | String(64) | NULL | 체크섬 |
| DESCRIPTION | Text | NULL | 설명 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| STARTED_AT | DateTime | default=now() | 시작 시간 |
| COMPLETED_AT | DateTime | NULL | 완료 시간 |
| UPDATED_AT | DateTime | onupdate=now() | 수정 시간 |

**인덱스**:
- PK: CHUNK_ID
- FK: PROGRAM_ID → PROGRAMS.PROGRAM_ID
- INDEX: PROGRAM_ID, DATA_TYPE, DATA_VERSION

**용도**:
- LLM 학습 데이터 분할 저장
- S3 기반 대용량 데이터 관리
- 데이터 버전 관리

---

### 17. TEMPLATES (템플릿)

**목적**: 프로그램 템플릿 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| TEMPLATE_ID | String(50) | PK | 템플릿 ID |
| DOCUMENT_ID | String(50) | FK, NOT NULL | 문서 ID |
| PROGRAM_ID | String(50) | FK, NULL | 프로그램 ID |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATED_AT | DateTime | NOT NULL, default=now() | 생성일시 |
| CREATED_BY | String(50) | NOT NULL | 생성자 |

**인덱스**:
- PK: TEMPLATE_ID
- FK: DOCUMENT_ID → DOCUMENTS.DOCUMENT_ID
- FK: PROGRAM_ID → PROGRAMS.PROGRAM_ID

**용도**:
- 템플릿 문서 관리
- 프로그램별 템플릿 연결

---

### 18. TEMPLATE_DATA (템플릿 데이터)

**목적**: 템플릿 상세 데이터 관리

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| TEMPLATE_DATA_ID | String(50) | PK | 템플릿 데이터 ID |
| TEMPLATE_ID | String(50) | FK, NOT NULL | 템플릿 ID |
| FOLDER_ID | String(100) | NULL | 폴더 ID |
| FOLDER_NAME | String(200) | NULL | 폴더명 |
| SUB_FOLDER_NAME | String(200) | NULL | 하위 폴더명 |
| LOGIC_ID | String(100) | NOT NULL | 로직 ID |
| LOGIC_NAME | String(200) | NOT NULL | 로직명 |
| DOCUMENT_ID | String(50) | FK, NULL | 문서 ID |
| ROW_INDEX | Integer | NOT NULL | 행 인덱스 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| STARTED_AT | DateTime | default=now() | 시작 시간 |
| COMPLETED_AT | DateTime | NULL | 완료 시간 |
| UPDATED_AT | DateTime | onupdate=now() | 수정 시간 |
| CREATED_AT | DateTime | NOT NULL, default=now() | 생성일시 |

**인덱스**:
- PK: TEMPLATE_DATA_ID
- FK: TEMPLATE_ID → TEMPLATES.TEMPLATE_ID
- FK: DOCUMENT_ID → DOCUMENTS.DOCUMENT_ID
- INDEX: TEMPLATE_ID, FOLDER_ID, LOGIC_ID

**용도**:
- 템플릿 세부 데이터 관리
- 로직별 폴더 구조 관리
- 문서 연결

---

### 19. KNOWLEDGE_REFERENCES (지식베이스 참조)

**목적**: Knowledge Base 참조 정보 관리 (매뉴얼, 용어집, PLC 레포)

| 컬럼명 | 타입 | 제약 | 설명 |
|--------|------|------|------|
| REFERENCE_ID | String(50) | PK | 참조 ID |
| REFERENCE_TYPE | String(50) | NOT NULL | 참조 타입 (manual/glossary/plc) |
| NAME | String(255) | NOT NULL | 이름 |
| VERSION | String(50) | NULL | 버전 |
| IS_LATEST | Boolean | NOT NULL, default=false | 최신 버전 여부 |
| REPO_ID | String(255) | NOT NULL | 레포지토리 ID |
| DATASOURCE_ID | String(255) | NOT NULL | 데이터소스 ID |
| FILE_ID | String(255) | NULL | 파일 ID |
| DESCRIPTION | Text | NULL | 설명 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| IS_ACTIVE | Boolean | NOT NULL, default=true | 활성 상태 |
| CREATED_AT | DateTime | NOT NULL, default=now() | 생성일시 |
| CREATED_BY | String(50) | NOT NULL | 생성자 |
| UPDATED_AT | DateTime | NULL, onupdate=now() | 수정일시 |
| UPDATED_BY | String(50) | NULL | 수정자 |

**참조 타입**:
- `manual` - 매뉴얼
- `glossary` - 용어집
- `plc` - PLC 레포지토리

**인덱스**:
- PK: REFERENCE_ID
- INDEX: REFERENCE_TYPE, REPO_ID, DATASOURCE_ID

**용도**:
- Knowledge Base 참조 관리
- 외부 레포지토리 연결
- 버전 관리

---

## 관계 및 제약조건

### Foreign Key 관계

```
CHATS
  └─ user_id → USERS.user_id

CHAT_MESSAGES
  ├─ chat_id → CHATS.chat_id
  └─ plc_id → PLC.id

MESSAGE_RATINGS
  └─ message_id → CHAT_MESSAGES.message_id

DOCUMENTS
  ├─ program_id → PROGRAMS.program_id
  ├─ source_document_id → DOCUMENTS.document_id (자기 참조)
  └─ knowledge_reference_id → KNOWLEDGE_REFERENCES.reference_id

DOCUMENT_CHUNKS
  └─ doc_id → DOCUMENTS.document_id (문자열 참조)

PROCESSING_JOBS
  └─ program_id → PROGRAMS.program_id

PROCESSING_FAILURES
  └─ program_id → PROGRAMS.program_id

PLC
  ├─ program_id → PROGRAMS.program_id (UNIQUE, 1:1)
  ├─ plant_id_current → PLANT_MASTER.plant_id
  ├─ process_id_current → PROCESS_MASTER.process_id
  ├─ line_id_current → LINE_MASTER.line_id
  └─ equipment_group_id_current → EQUIPMENT_GROUP_MASTER.equipment_group_id

PROCESS_MASTER
  └─ plant_id → PLANT_MASTER.plant_id

LINE_MASTER
  └─ process_id → PROCESS_MASTER.process_id

EQUIPMENT_GROUP_MASTER
  └─ line_id → LINE_MASTER.line_id

PROGRAM_LLM_DATA_CHUNKS
  └─ program_id → PROGRAMS.program_id

TEMPLATES
  ├─ document_id → DOCUMENTS.document_id
  └─ program_id → PROGRAMS.program_id

TEMPLATE_DATA
  ├─ template_id → TEMPLATES.template_id
  └─ document_id → DOCUMENTS.document_id
```

### Unique 제약

- USERS.employee_id
- MESSAGE_RATINGS.message_id
- DOCUMENT_CHUNKS.chunk_id
- PROCESSING_JOBS.job_id
- PLC.program_id (프로그램당 1개 PLC)
- PLANT_MASTER.plant_code
- PROCESS_MASTER.process_code
- LINE_MASTER.line_code
- EQUIPMENT_GROUP_MASTER.equipment_group_code

---

## 인덱스 전략

### 1. 성능 최적화 인덱스

#### 채팅 조회 (빈번한 쿼리)
```sql
CREATE INDEX idx_chat_messages_chat_id_create_dt 
  ON CHAT_MESSAGES(chat_id, create_dt DESC);

CREATE INDEX idx_chats_user_id_create_dt 
  ON CHATS(user_id, create_dt DESC);
```

#### 문서 검색
```sql
CREATE INDEX idx_documents_user_status 
  ON DOCUMENTS(user_id, status, document_type);

CREATE INDEX idx_documents_program 
  ON DOCUMENTS(program_id) 
  WHERE program_id IS NOT NULL;
```

#### PLC 및 기준정보
```sql
CREATE INDEX idx_plc_program_mapping 
  ON PLC(program_id) 
  WHERE program_id IS NOT NULL;

CREATE INDEX idx_plc_hierarchy 
  ON PLC(plant_id_current, process_id_current, line_id_current);
```

### 2. 복합 인덱스

#### 실패 처리 조회
```sql
CREATE INDEX idx_failures_program_type_status 
  ON PROCESSING_FAILURES(program_id, failure_type, status);
```

#### 청크 조회
```sql
CREATE INDEX idx_chunks_doc_page 
  ON DOCUMENT_CHUNKS(doc_id, page_number, chunk_type);
```

### 3. 부분 인덱스 (Partial Index)

#### 활성 상태만 인덱싱
```sql
CREATE INDEX idx_users_active 
  ON USERS(user_id) 
  WHERE is_active = true AND is_deleted = false;

CREATE INDEX idx_documents_processing 
  ON DOCUMENTS(document_id, status) 
  WHERE status IN ('processing', 'preparing');
```

---

## 데이터 타입 선택 기준

### String 길이
- ID: String(50) - UUID 및 생성된 ID
- 코드: String(50) - 기준정보 코드
- 이름: String(100-255) - 일반 이름
- 경로: String(500-1000) - 파일 경로, URL
- 텍스트: Text - 제한 없는 긴 텍스트

### 날짜/시간
- CREATE_DT: DateTime with server_default=now()
- UPDATE_DT: DateTime with onupdate=now()
- Timestamp 필드: UTC 기준

### Boolean
- 기본값 지정: server_default=true()/false()
- NULL 허용하지 않음

### JSON
- 동적 메타데이터
- 배열 데이터 (권한, 리스트)
- 확장 가능한 설정

---

## 마이그레이션 전략

### Alembic 사용
```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "description"

# 마이그레이션 실행
alembic upgrade head

# 롤백
alembic downgrade -1
```

### 주의사항
1. **Foreign Key 순서**: 참조되는 테이블 먼저 생성
2. **인덱스 순서**: 테이블 생성 후 인덱스 추가
3. **데이터 마이그레이션**: 별도 스크립트 작성
4. **백업**: 마이그레이션 전 반드시 백업

---

## 성능 고려사항

### 1. 쿼리 최적화
- SELECT 시 필요한 컬럼만 조회
- JOIN 최소화
- 인덱스 활용

### 2. 캐싱 전략
- Redis 캐싱 활용
- 자주 조회되는 데이터 캐싱
- TTL 설정

### 3. 파티셔닝 (향후)
- 채팅 메시지: 날짜별 파티셔닝
- 문서: 사용자별 파티셔닝
- 로그: 월별 파티셔닝

### 4. 아카이빙
- 오래된 채팅 메시지 아카이빙
- 삭제된 문서 아카이빙
- 실패 로그 정리

---

**최종 업데이트**: 2025-11-13
**문서 버전**: 1.1.0
