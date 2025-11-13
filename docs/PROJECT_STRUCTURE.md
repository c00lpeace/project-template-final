# 📂 프로젝트 구조 상세 가이드

## 목차
- [전체 디렉토리 구조](#전체-디렉토리-구조)
- [ai_backend 구조](#ai_backend-구조)
- [doc_processor 구조](#doc_processor-구조)
- [shared_core 구조](#shared_core-구조)
- [주요 파일 설명](#주요-파일-설명)
- [설정 파일](#설정-파일)

---

## 전체 디렉토리 구조

```
D:\project-template-final\
│
├── 📁 ai_backend/                  # FastAPI 백엔드 애플리케이션
│   ├── src/                        # 소스 코드
│   ├── k8s/                        # Kubernetes 배포 설정
│   ├── uploads/                    # 업로드 파일 저장소
│   ├── requirements.txt            # Python 의존성
│   └── *.md                        # 문서들
│
├── 📁 doc_processor/               # Prefect 문서 처리 파이프라인
│   ├── flow/                       # Prefect Flow 정의
│   ├── base/                       # Prefect 서버/워커 관리
│   ├── k8s/                        # Kubernetes 배포 설정
│   ├── requirements.txt            # Python 의존성
│   └── README.md                   # 문서
│
├── 📁 shared_core/                 # 공통 모듈
│   ├── models.py                   # 공통 데이터베이스 모델
│   ├── plc_models.py               # PLC 관련 모델
│   ├── crud.py                     # 공통 CRUD
│   ├── services.py                 # 공통 서비스
│   ├── database.py                 # 데이터베이스 연결
│   └── requirements.txt            # Python 의존성
│
├── 📁 k8s-infra/                   # 인프라 Kubernetes 설정
│   ├── dev-postgres.yaml           # PostgreSQL
│   ├── dev-redis.yaml              # Redis
│   └── dev-milvus.yaml             # Milvus
│
├── 📁 docs/                        # 프로젝트 문서
│   ├── PROJECT_OVERVIEW.md         # 프로젝트 개요
│   ├── DATABASE_SCHEMA.md          # 데이터베이스 스키마
│   ├── API_DOCUMENTATION.md        # API 문서
│   └── PROJECT_STRUCTURE.md        # 이 파일
│
├── 📁 .vscode/                     # VSCode 설정
│   ├── settings.json               # 편집기 설정
│   ├── launch.json                 # 디버깅 설정
│   └── tasks.json                  # 태스크 설정
│
├── .gitignore                      # Git 무시 파일
├── README.md                       # 프로젝트 README
├── deploy-dev.sh                   # 개발 환경 배포 스크립트
├── prepare-wheels.sh               # Python 패키지 준비
└── DEPLOYMENT_GUIDE_OFFLINE.md     # 오프라인 배포 가이드
```

---

## ai_backend 구조

### 전체 구조
```
ai_backend/
│
├── 📁 src/                         # 애플리케이션 소스
│   ├── 📁 api/                     # API 계층
│   ├── 📁 cache/                   # 캐싱 계층
│   ├── 📁 config/                  # 설정 관리
│   ├── 📁 core/                    # 핵심 컴포넌트
│   ├── 📁 database/                # 데이터베이스 계층
│   ├── 📁 middleware/              # 미들웨어
│   ├── 📁 types/                   # 타입 정의
│   ├── 📁 utils/                   # 유틸리티
│   └── main.py                     # 애플리케이션 진입점
│
├── 📁 k8s/                         # Kubernetes 설정
│   ├── 📁 overlays/                # Kustomize 오버레이
│   ├── configmap.yaml              # ConfigMap
│   ├── deployment.yaml             # Deployment
│   ├── service.yaml                # Service
│   ├── ingress.yaml                # Ingress
│   └── deploy.sh                   # 배포 스크립트
│
├── 📁 uploads/                     # 파일 업로드 디렉토리
│   ├── user/                       # 사용자 업로드
│   └── viewer/                     # 뷰어 캐시
│
├── requirements.txt                # Python 의존성
├── requirements-freeze.txt         # 고정된 의존성
├── Dockerfile                      # Docker 이미지
├── Dockerfile.dev                  # 개발용 Docker
├── logging.conf                    # 로깅 설정
├── llm_chat_client.html            # 웹 클라이언트
└── *.md                            # 문서들
```

### src/ 상세 구조

#### api/ - API 계층
```
api/
├── routers/                        # API 라우터
│   ├── chat_router.py              # 채팅 API
│   ├── user_router.py              # 사용자 API
│   ├── document_router.py          # 문서 API
│   ├── group_router.py             # 그룹 API
│   ├── rating_router.py            # 평가 API
│   ├── program_router.py           # 프로그램 API
│   ├── plc_router.py               # PLC API
│   └── cache_router.py             # 캐시 API
│
└── services/                       # 비즈니스 로직
    ├── llm_chat_service.py         # 채팅 서비스
    ├── user_service.py             # 사용자 서비스
    ├── document_service.py         # 문서 서비스
    ├── group_service.py            # 그룹 서비스
    ├── program_service.py          # 프로그램 서비스
    ├── program_uploader.py         # 프로그램 업로더
    ├── program_validator.py        # 프로그램 검증
    ├── llm_provider_factory.py     # LLM 제공자 팩토리
    ├── knowledge_status_service.py # 지식 상태 서비스
    ├── progress_update_service.py  # 진행상황 업데이트 서비스
    └── s3_download_service.py      # S3 다운로드 서비스
```

#### database/ - 데이터베이스 계층
```
database/
├── models/                         # SQLAlchemy 모델
│   ├── user_models.py              # 사용자 모델
│   ├── chat_models.py              # 채팅 모델
│   ├── document_models.py          # 문서 모델 (shared_core 사용)
│   ├── program_models.py           # 프로그램 모델 (shared_core 사용)
│   ├── group_models.py             # 그룹 모델
│   ├── knowledge_reference_models.py # 지식 참조 모델
│   ├── master_models.py            # 마스터 데이터 모델
│   ├── plc_models.py               # PLC 모델
│   ├── plc_history_models.py       # PLC 히스토리 모델
│   └── template_models.py          # 템플릿 모델
│
├── crud/                           # CRUD 작업
│   ├── user_crud.py                # 사용자 CRUD
│   ├── chat_crud.py                # 채팅 CRUD
│   ├── document_crud.py            # 문서 CRUD
│   ├── program_crud.py             # 프로그램 CRUD
│   ├── group_crud.py               # 그룹 CRUD
│   ├── rating_crud.py              # 평가 CRUD
│   ├── program_failure_crud.py     # 프로그램 실패 CRUD
│   ├── knowledge_reference_crud.py # 지식 참조 CRUD
│   ├── master_crud.py              # 마스터 데이터 CRUD
│   ├── plc_crud.py                 # PLC CRUD
│   └── template_crud.py            # 템플릿 CRUD
│
└── base.py                         # 데이터베이스 Base 클래스
```

#### types/ - 타입 정의
```
types/
├── enums/                          # Enum 타입
│   ├── base.py                     # 기본 Enum
│   └── query.py                    # 쿼리 Enum
│
├── request/                        # 요청 타입
│   ├── chat_request.py             # 채팅 요청
│   ├── user_request.py             # 사용자 요청
│   ├── group_request.py            # 그룹 요청
│   ├── program_request.py          # 프로그램 요청
│   └── rating_request.py           # 평가 요청
│
└── response/                       # 응답 타입
    ├── base.py                     # 기본 응답
    ├── chat_response.py            # 채팅 응답
    ├── user_response.py            # 사용자 응답
    ├── group_response.py           # 그룹 응답
    ├── program_response.py         # 프로그램 응답
    ├── rating_response.py          # 평가 응답
    ├── plc_response.py             # PLC 응답
    ├── response_code.py            # 응답 코드
    └── exceptions.py               # 예외 타입
```

#### config/ - 설정 관리
```
config/
└── simple_settings.py              # Pydantic Settings 기반 설정
```

#### core/ - 핵심 컴포넌트
```
core/
├── dependencies.py                 # FastAPI 의존성
└── global_exception_handlers.py    # 전역 예외 처리
```

#### cache/ - 캐싱 계층
```
cache/
└── redis_client.py                 # Redis 클라이언트
```

#### middleware/ - 미들웨어
```
middleware/
└── performance_middleware.py       # 성능 모니터링
```

#### utils/ - 유틸리티
```
utils/
├── logging_utils.py                # 로깅 유틸
└── uuid_gen.py                     # UUID 생성기
```

---

## doc_processor 구조

```
doc_processor/
│
├── 📁 flow/                        # Prefect Flow
│   ├── document_processing_pipeline.py  # 단일 문서 처리
│   ├── batch_document_processing_pipeline.py  # 배치 처리
│   ├── PDFGenerator.py             # PDF 생성 (테스트)
│   ├── PDFTest.py                  # PDF 테스트
│   ├── config.py                   # 설정
│   └── database.py                 # 데이터베이스
│
├── 📁 base/                        # Prefect 관리
│   ├── start_prefect_server.py     # 서버 시작
│   ├── start_worker.py             # 워커 시작
│   └── deploy_pipeline.py          # 파이프라인 배포
│
├── 📁 k8s/                         # Kubernetes 설정
│   ├── 1-prefect-server-deployment.yaml
│   ├── 2-flow-registration-job.yaml
│   ├── 3-prefect-worker-deployment.yaml
│   ├── 4-pipeline-deployment-job.yaml
│   ├── configmap.yaml
│   ├── namespace.yaml
│   └── service-account.yaml
│
├── run_document_pipeline.py        # 파이프라인 실행
├── run_batch_pipeline.py           # 배치 실행
├── run_search.py                   # 검색 실행
├── requirements.txt                # Python 의존성
├── requirements-freeze.txt         # 고정된 의존성
├── prefect.yaml                    # Prefect 설정
└── Dockerfile.dev                  # 개발용 Docker
```

### Flow 상세

#### document_processing_pipeline.py
- **목적**: 단일 문서 처리
- **단계**:
  1. PDF 텍스트 추출
  2. 이미지 캡처
  3. GPT-4 Vision 이미지 분석
  4. 텍스트 + 이미지 설명 통합
  5. OpenAI Embeddings 생성
  6. Milvus 저장
  7. 상태 업데이트

#### batch_document_processing_pipeline.py
- **목적**: 대량 문서 일괄 처리
- **특징**:
  - 병렬 처리 지원
  - 실패 로깅
  - 재시도 메커니즘

---

## shared_core 구조

```
shared_core/
│
├── models.py                       # 공통 모델
│   ├── Document                    # 문서 모델
│   ├── DocumentChunk               # 문서 청크
│   └── ProcessingJob               # 처리 작업
│
├── plc_models.py                   # PLC 관련 모델
│   ├── Program                     # 프로그램
│   ├── ProcessingFailure           # 처리 실패
│   ├── PLC                         # PLC 정보
│   ├── PlantMaster                 # 공장 기준정보
│   ├── ProcessMaster               # 공정 기준정보
│   ├── LineMaster                  # 라인 기준정보
│   ├── EquipmentGroupMaster        # 장비그룹 기준정보
│   ├── ProgramLLMDataChunk         # 프로그램 LLM 데이터
│   ├── Template                    # 템플릿
│   ├── TemplateData                # 템플릿 데이터
│   └── KnowledgeReference          # 지식 참조
│
├── crud.py                         # 공통 CRUD
│   ├── DocumentCRUD                # 문서 CRUD
│   ├── DocumentChunkCRUD           # 청크 CRUD
│   └── ProcessingJobCRUD           # 작업 CRUD
│
├── services.py                     # 공통 서비스
│   ├── DocumentService             # 문서 서비스
│   ├── DocumentChunkService        # 청크 서비스
│   └── ProcessingJobService        # 작업 서비스
│
├── database.py                     # 데이터베이스 연결
│   ├── DatabaseManager             # DB 관리자
│   └── get_db_session()            # 세션 생성
│
├── __init__.py                     # 패키지 초기화
├── requirements.txt                # Python 의존성
└── README.md                       # 문서
```

---

## 주요 파일 설명

### 1. ai_backend/src/main.py
**목적**: FastAPI 애플리케이션 진입점

**주요 기능**:
- FastAPI 앱 생성
- 라우터 등록
- 미들웨어 설정
- 전역 예외 처리
- CORS 설정
- 로깅 설정

**코드 구조**:
```python
def create_app():
    app = FastAPI(...)
    
    # 라우터 추가
    app.include_router(chat_router, prefix="/v1")
    app.include_router(user_router, prefix="/v1")
    
    # 미들웨어 추가
    app.add_middleware(CORSMiddleware, ...)
    
    # 예외 처리
    app = set_global_exception_handlers(app)
    
    return app
```

---

### 2. ai_backend/src/config/simple_settings.py
**목적**: 설정 관리

**주요 클래스**:
```python
class Settings(BaseSettings):
    # Application
    app_version: str
    app_locale: str
    app_debug: bool
    
    # Database
    database_host: str
    database_port: int
    
    # OpenAI
    openai_api_key: str
    openai_model: str
    
    # Cache
    cache_enabled: bool
    redis_host: str
```

---

### 3. shared_core/models.py
**목적**: 공통 데이터베이스 모델

**주요 모델**:
```python
class Document(Base):
    __tablename__ = "DOCUMENTS"
    document_id = Column(String(50), primary_key=True)
    document_name = Column(String(255), nullable=False)
    # ...

class DocumentChunk(Base):
    __tablename__ = "DOCUMENT_CHUNKS"
    id = Column(UUID, primary_key=True)
    chunk_id = Column(String(255), unique=True)
    # ...

class ProcessingJob(Base):
    __tablename__ = "PROCESSING_JOBS"
    id = Column(UUID, primary_key=True)
    job_id = Column(String(255), unique=True)
    # ...
```

---

### 4. doc_processor/flow/document_processing_pipeline.py
**목적**: 문서 처리 Prefect Flow

**주요 함수**:
```python
@flow(name="document-processing-pipeline")
def document_processing_pipeline(document_id: str):
    # 1. 문서 로드
    # 2. 텍스트 추출
    # 3. 이미지 처리
    # 4. 임베딩 생성
    # 5. Milvus 저장
    pass
```

---

## 설정 파일

### 1. .env (로컬 개발용)
```bash
# Application
APP_VERSION=1.0.0
APP_DEBUG=true

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=chat_db
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=password

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# Cache
CACHE_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_TO_FILE=true
LOG_DIR=./logs
LOG_LEVEL=debug
```

---

### 2. k8s/configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-backend-config
data:
  APP_VERSION: "1.0.0"
  DATABASE_HOST: "postgres-service"
  DATABASE_PORT: "5432"
  OPENAI_API_KEY: "sk-..."
  CACHE_ENABLED: "true"
  REDIS_HOST: "redis-service"
```

---

### 3. requirements.txt
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==1.4.48
psycopg2-binary==2.9.9
redis==5.0.1
openai==1.12.0
pydantic==2.6.0
pydantic-settings==2.1.0
```

---

### 4. Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 개발 워크플로우

### 1. 로컬 개발
```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일 편집

# 4. 서버 실행
python -m uvicorn src.main:app --reload
```

---

### 2. Docker 개발
```bash
# 1. 이미지 빌드
docker build -t ai-backend:dev -f Dockerfile.dev .

# 2. 컨테이너 실행
docker run -p 8000:8000 \
  -e DATABASE_HOST=host.docker.internal \
  -e OPENAI_API_KEY=sk-... \
  ai-backend:dev
```

---

### 3. Kubernetes 배포
```bash
# 1. ConfigMap 적용
kubectl apply -f k8s/configmap.yaml

# 2. Deployment 적용
kubectl apply -f k8s/deployment.yaml

# 3. Service 적용
kubectl apply -f k8s/service.yaml

# 4. Ingress 적용
kubectl apply -f k8s/ingress.yaml
```

---

## 디렉토리 명명 규칙

### 1. 코드 디렉토리
- **소문자 + 언더스코어**: `api/`, `database/`, `utils/`
- **복수형**: `routers/`, `models/`, `services/`

### 2. 설정 디렉토리
- **소문자 + 하이픈**: `k8s/`, `k8s-infra/`

### 3. 파일 명명
- **Python**: `snake_case.py`
- **Config**: `kebab-case.yaml`
- **Docker**: `Dockerfile`, `Dockerfile.dev`

---

## 파일 크기 가이드

### 권장 파일 크기
- **Python 모듈**: < 500 lines
- **API 라우터**: < 300 lines
- **서비스**: < 500 lines
- **CRUD**: < 300 lines

### 분할 기준
- 1000 lines 초과 시 분할 고려
- 기능별로 분할
- 단일 책임 원칙 준수

---

## 확장 가이드

### 1. 새 API 엔드포인트 추가
```bash
src/api/routers/
└── new_router.py           # 1. 라우터 생성

src/api/services/
└── new_service.py          # 2. 서비스 생성

src/database/models/
└── new_models.py           # 3. 모델 생성 (필요시)

src/database/crud/
└── new_crud.py             # 4. CRUD 생성

src/types/request/
└── new_request.py          # 5. 요청 타입

src/types/response/
└── new_response.py         # 6. 응답 타입

src/main.py                 # 7. 라우터 등록
```

---

### 2. 새 Prefect Flow 추가
```bash
doc_processor/flow/
└── new_pipeline.py         # 1. Flow 생성

doc_processor/base/
└── deploy_new_pipeline.py  # 2. 배포 스크립트

doc_processor/
└── run_new_pipeline.py     # 3. 실행 스크립트
```

---

## 정리 규칙

### 1. 코드 정리
- 미사용 import 제거
- 미사용 변수 제거
- 주석 업데이트

### 2. 파일 정리
- 미사용 파일 삭제
- 테스트 파일 정리
- 로그 파일 정리

### 3. 의존성 정리
```bash
# 실제 사용 패키지만 남기기
pip freeze > requirements.txt
```

---

## 📝 변경 이력

### 2025-11-13
- **추가된 서비스**:
  - `knowledge_status_service.py` - 지식 상태 서비스
  - `progress_update_service.py` - 진행상황 업데이트 서비스
  - `s3_download_service.py` - S3 다운로드 서비스

- **추가된 모델**:
  - `knowledge_reference_models.py` - 지식 참조 모델
  - `master_models.py` - 마스터 데이터 모델
  - `plc_history_models.py` - PLC 히스토리 모델
  - `template_models.py` - 템플릿 모델

- **추가된 CRUD**:
  - `master_crud.py` - 마스터 데이터 CRUD
  - `plc_crud.py` - PLC CRUD
  - `template_crud.py` - 템플릿 CRUD
  - `program_failure_crud.py` - 프로그램 실패 CRUD (파일명 변경)

- **파일명 변경**:
  - `processing_failure_crud.py` → `program_failure_crud.py`

---

**최종 업데이트**: 2025-11-13
**문서 버전**: 1.1.0
