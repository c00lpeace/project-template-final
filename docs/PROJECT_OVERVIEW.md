# 📄 프로젝트 전체 개요

## 🎯 프로젝트 목적

통합 문서 처리 및 AI 챗봇 시스템 - FastAPI 백엔드와 Prefect 기반 문서 임베딩 파이프라인을 통합한 엔터프라이즈급 AI 문서 처리 플랫폼

## 🏗️ 전체 아키텍처

```
project-template-final/
│
├── 📦 ai_backend/              # FastAPI 백엔드 서버
│   ├── src/                    # 소스 코드
│   │   ├── api/               # API 라우터 및 서비스
│   │   ├── database/          # 데이터베이스 모델 및 CRUD
│   │   ├── cache/             # Redis 캐싱
│   │   ├── config/            # 설정 관리
│   │   └── middleware/        # 미들웨어
│   ├── k8s/                   # Kubernetes 배포 설정
│   └── uploads/               # 업로드된 파일
│
├── 🔄 doc_processor/          # Prefect 문서 처리 파이프라인
│   ├── flow/                  # Prefect Flow 정의
│   ├── base/                  # Prefect 서버/워커 시작 스크립트
│   └── k8s/                   # Kubernetes 배포 설정
│
├── 🔗 shared_core/            # 공통 모듈 (Backend ↔ Processor)
│   ├── models.py              # 공통 데이터베이스 모델
│   ├── plc_models.py          # PLC 및 Program 모델
│   ├── crud.py                # 공통 CRUD 작업
│   └── services.py            # 공통 비즈니스 로직
│
├── 🛠️ k8s-infra/             # 인프라 Kubernetes 설정
│   ├── dev-postgres.yaml      # PostgreSQL 개발 환경
│   ├── dev-redis.yaml         # Redis 개발 환경
│   └── dev-milvus.yaml        # Milvus 벡터 DB 개발 환경
│
└── 📚 docs/                   # 프로젝트 문서
    ├── PROJECT_OVERVIEW.md    # 이 파일
    ├── DATABASE_SCHEMA.md     # 데이터베이스 스키마
    └── API_DOCUMENTATION.md   # API 문서
```

## 🎨 기술 스택

### Backend (ai_backend)
- **Framework**: FastAPI 0.109+
- **ORM**: SQLAlchemy 1.4+
- **Database**: PostgreSQL 12+
- **Cache**: Redis 7.0+
- **Python**: 3.12+
- **Settings**: Pydantic Settings
- **LLM**: OpenAI, Azure OpenAI

### Document Processor (doc_processor)
- **Workflow**: Prefect 2.x
- **Document**: PyPDF2, python-docx
- **Vector DB**: Milvus
- **Embedding**: OpenAI Embeddings
- **Vision**: GPT-4 Vision

### Shared Core (shared_core)
- **ORM**: SQLAlchemy 1.4+
- **공통 모델**: Document, Program, PLC 등
- **공통 CRUD**: 재사용 가능한 데이터베이스 작업

### Infrastructure
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: (추후 정의)

## 🌟 주요 기능

### 1. AI 채팅 서비스 (ai_backend)
- **실시간 스트리밍 채팅**: OpenAI/Azure OpenAI 기반
- **대화 이력 관리**: 채팅방 및 메시지 관리
- **사용자 관리**: 사용자 및 권한 관리
- **그룹 관리**: 사이트별 권한 관리
- **문서 업로드**: 파일 업로드 및 메타데이터 관리
- **캐시 시스템**: Redis 기반 고성능 캐싱
- **평가 시스템**: AI 응답 품질 평가

### 2. 문서 처리 파이프라인 (doc_processor)
- **자동 문서 처리**: PDF/DOCX 파일 자동 처리
- **텍스트 추출**: 페이지별 텍스트 추출
- **이미지 분석**: GPT-4 Vision 기반 이미지 설명 생성
- **벡터 임베딩**: OpenAI Embeddings 생성
- **벡터 저장**: Milvus 벡터 데이터베이스 저장
- **배치 처리**: 대량 문서 일괄 처리
- **실패 처리**: 자동 재시도 및 실패 로깅

### 3. PLC 프로그램 관리
- **프로그램 업로드**: PLC 프로그램 파일 업로드
- **프로그램 처리**: 자동 파싱 및 분석
- **Template 관리**: 프로그램 템플릿 관리
- **Knowledge Base**: 매뉴얼, 용어집, PLC 레포 참조
- **기준정보 관리**: Plant, Process, Line, Equipment Group

## 🔄 데이터 흐름

### 문서 처리 워크플로우

```
1. 파일 업로드 (FastAPI)
   ↓
2. Document 메타데이터 저장 (PostgreSQL)
   ↓
3. Prefect 파이프라인 트리거
   ↓
4. PDF 텍스트 추출
   ↓
5. 이미지 캡처 및 GPT-4 Vision 분석
   ↓
6. 텍스트 + 이미지 설명 통합
   ↓
7. OpenAI Embeddings 생성
   ↓
8. Milvus 벡터 DB 저장
   ↓
9. 문서 상태 업데이트 (completed)
```

### 채팅 워크플로우

```
1. 사용자 메시지 입력
   ↓
2. 캐시 확인 (Redis)
   ↓
3. LLM API 호출 (OpenAI/Azure)
   ↓
4. 스트리밍 응답 반환
   ↓
5. 메시지 저장 (PostgreSQL)
   ↓
6. 캐시 업데이트
```

## 🔐 보안 및 권한

### 사용자 인증
- 사용자 ID 기반 인증
- 사번(Employee ID) 기반 인증

### 권한 관리
- **문서 권한**: 공개/비공개, 권한 리스트
- **그룹 권한**: SIT Auth, NCT Auth, 서비스 권한
- **사용자 권한**: 사이트 리스트 기반

### 데이터 접근 제어
- 사용자별 문서 접근 제어
- 그룹별 권한 필터링
- PLC 정보 접근 제어

## 📊 모니터링 및 로깅

### 로깅 시스템
- **파일 로깅**: TimedRotatingFileHandler (선택적)
- **콘솔 로깅**: Coloredlogs (기본)
- **로그 레벨**: DEBUG, INFO, WARNING, ERROR
- **로그 로테이션**: 일별/주별/월별
- **로그 보관**: 설정 가능한 보관 기간

### 성능 모니터링
- API 응답 시간
- 캐시 히트율
- 데이터베이스 쿼리 성능
- LLM API 호출 시간

### 예외 처리
- 계층별 예외 처리 (Router → Service → CRUD)
- 전역 예외 핸들러
- 사용자 친화적 에러 메시지
- 자세한 에러 로깅

## 🚀 배포 환경

### 로컬 개발 환경
```bash
# 1. 의존성 설치
cd ai_backend
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 편집

# 3. 서버 실행
python -m uvicorn src.main:app --reload
```

### Kubernetes 배포
```bash
# 1. 인프라 배포
kubectl apply -f k8s-infra/

# 2. Backend 배포
kubectl apply -f ai_backend/k8s/

# 3. Document Processor 배포
kubectl apply -f doc_processor/k8s/
```

## 📚 관련 문서

### 핵심 가이드
- [데이터베이스 스키마](DATABASE_SCHEMA.md) - 전체 ERD 및 테이블 구조
- [API 문서](API_DOCUMENTATION.md) - REST API 엔드포인트 및 사용법
- [Exception 처리 가이드](../ai_backend/EXCEPTION_GUIDE.md) - 예외 처리 전략
- [설정 가이드](../ai_backend/CONFIG_GUIDE.md) - Pydantic Settings 사용법
- [로깅 가이드](../ai_backend/LOGGING_GUIDE.md) - 로깅 시스템 구성
- [캐시 가이드](../ai_backend/CACHE_CONTROL.md) - Redis 캐싱 전략

### 세부 문서
- [LLM Provider 가이드](../ai_backend/LLM_PROVIDER_GUIDE.md) - OpenAI/Azure OpenAI 설정
- [프로그램 플로우](../ai_backend/PROGRAM_FLOW.md) - 전체 프로그램 흐름
- [재시도 전략](../ai_backend/RETRY_STRATEGY.md) - 실패 처리 및 재시도
- [Preprocessing 전략](../ai_backend/PREPROCESSING_STRATEGY.md) - 문서 전처리

## 🤝 기여 가이드

### 코드 스타일
- **Python**: PEP 8
- **Import 순서**: 표준 라이브러리 → 서드파티 → 로컬
- **주석**: 한글 또는 영어
- **Docstring**: Google Style

### 커밋 메시지
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드, 설정 변경
```

### Pull Request
1. Feature 브랜치 생성
2. 변경사항 커밋
3. 테스트 작성 및 실행
4. PR 생성 및 리뷰 요청

## 📞 지원 및 문의

### 문제 보고
- GitHub Issues 사용
- 상세한 재현 방법 포함
- 로그 파일 첨부

### 기술 지원
- 내부 기술 지원팀 문의
- 프로젝트 문서 참조

## 📄 라이선스

내부 프로젝트 - 비공개

---

**최종 업데이트**: 2025-11-11
**문서 버전**: 1.0.0
