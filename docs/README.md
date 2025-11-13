# 📚 프로젝트 문서 인덱스

이 디렉토리는 프로젝트의 모든 문서를 포함합니다.

## 📖 문서 목록

### 1. [프로젝트 개요](PROJECT_OVERVIEW.md)
**프로젝트의 전체적인 개요와 아키텍처**
- 프로젝트 목적 및 주요 기능
- 기술 스택
- 전체 아키텍처
- 데이터 흐름
- 보안 및 권한 체계
- 배포 환경

**👉 신규 팀원이라면 여기서 시작하세요!**

---

### 2. [데이터베이스 스키마](DATABASE_SCHEMA.md)
**데이터베이스 구조 및 ERD**
- 전체 ERD (Entity Relationship Diagram)
- 19개 테이블 상세 설명
- Foreign Key 관계
- 인덱스 전략
- 마이그레이션 가이드

**👉 데이터베이스 작업 전에 필독!**

---

### 3. [API 문서](API_DOCUMENTATION.md)
**REST API 엔드포인트 및 사용법**
- 채팅 API (10개 엔드포인트)
- 사용자 API (11개 엔드포인트)
- 문서 관리 API (21개 엔드포인트)
- 예제 코드 (Python, JavaScript, cURL)
- 에러 코드

**👉 API 사용 시 참조하세요!**

---

### 4. [프로젝트 구조](PROJECT_STRUCTURE.md)
**디렉토리 구조 및 파일 설명**
- 전체 디렉토리 구조
- ai_backend 상세 구조
- doc_processor 상세 구조
- shared_core 상세 구조
- 주요 파일 설명
- 개발 워크플로우

**👉 코드 네비게이션 가이드!**

---

## 🚀 빠른 시작

### 개발자 온보딩 순서
1. **[프로젝트 개요](PROJECT_OVERVIEW.md)** 읽기 (10분)
2. **[프로젝트 구조](PROJECT_STRUCTURE.md)** 파악 (15분)
3. **[데이터베이스 스키마](DATABASE_SCHEMA.md)** 이해 (20분)
4. **[API 문서](API_DOCUMENTATION.md)** 참조 (필요시)

### 작업별 가이드

#### 백엔드 개발
```
1. PROJECT_OVERVIEW.md - 전체 이해
2. PROJECT_STRUCTURE.md - 코드 구조
3. DATABASE_SCHEMA.md - 데이터베이스
4. API_DOCUMENTATION.md - API 설계
```

#### 프론트엔드 개발
```
1. PROJECT_OVERVIEW.md - 시스템 이해
2. API_DOCUMENTATION.md - API 사용법
3. 예제 코드 참조
```

#### DevOps
```
1. PROJECT_OVERVIEW.md - 배포 환경
2. PROJECT_STRUCTURE.md - 디렉토리 구조
3. Kubernetes 설정 파일
```

---

## 📂 추가 문서 (ai_backend/)

프로젝트 루트의 `ai_backend/` 디렉토리에도 중요한 문서들이 있습니다:

### 핵심 가이드
- **[Exception 처리 가이드](../ai_backend/EXCEPTION_GUIDE.md)** - 계층별 예외 처리 전략
- **[설정 가이드](../ai_backend/CONFIG_GUIDE.md)** - Pydantic Settings 사용법
- **[로깅 가이드](../ai_backend/LOGGING_GUIDE.md)** - 로깅 시스템 구성
- **[캐시 가이드](../ai_backend/CACHE_CONTROL.md)** - Redis 캐싱 전략

### 세부 문서
- **[LLM Provider 가이드](../ai_backend/LLM_PROVIDER_GUIDE.md)** - OpenAI/Azure OpenAI
- **[프로그램 플로우](../ai_backend/PROGRAM_FLOW.md)** - 전체 프로그램 흐름
- **[재시도 전략](../ai_backend/RETRY_STRATEGY.md)** - 실패 처리 및 재시도
- **[Preprocessing 전략](../ai_backend/PREPROCESSING_STRATEGY.md)** - 문서 전처리
- **[Complete ERD](../ai_backend/COMPLETE_ERD.md)** - 상세 ERD

---

## 🔍 검색 팁

### 키워드로 찾기

**API 관련**:
- `POST`, `GET`, `DELETE` → API_DOCUMENTATION.md
- `endpoint`, `request`, `response` → API_DOCUMENTATION.md

**데이터베이스 관련**:
- `table`, `column`, `foreign key` → DATABASE_SCHEMA.md
- `USERS`, `CHATS`, `DOCUMENTS` → DATABASE_SCHEMA.md

**구조 관련**:
- `directory`, `file`, `module` → PROJECT_STRUCTURE.md
- `router`, `service`, `crud` → PROJECT_STRUCTURE.md

**아키텍처 관련**:
- `architecture`, `flow`, `component` → PROJECT_OVERVIEW.md

---

## 📝 문서 기여 가이드

### 문서 수정 시
1. 해당 문서 파일 수정
2. 변경 이력 업데이트
3. 마지막 업데이트 날짜 갱신

### 새 문서 추가 시
1. `docs/` 디렉토리에 파일 생성
2. 이 README에 링크 추가
3. 관련 문서에 상호 링크 추가

### 문서 스타일 가이드
- **제목**: `# 📚 제목` 형식
- **섹션**: `## 섹션명` 형식
- **코드 블록**: 언어 지정 (```python, ```bash 등)
- **강조**: `**굵게**`, `*기울임*`
- **링크**: `[텍스트](파일.md)`

---

## 🆘 도움말

### 문서를 찾을 수 없을 때
1. 이 README의 목록 확인
2. 키워드로 검색
3. GitHub에서 파일 검색
4. 팀에 문의

### 문서가 오래되었을 때
1. Issue 생성
2. 문서 담당자에게 알림
3. PR 제출

---

## 📊 문서 통계

| 문서 | 페이지 수 | 주요 내용 | 최종 업데이트 |
|------|-----------|----------|--------------|
| PROJECT_OVERVIEW.md | ~15 | 프로젝트 개요 | 2025-11-11 |
| DATABASE_SCHEMA.md | ~40 | DB 스키마 | 2025-11-13 |
| API_DOCUMENTATION.md | ~35 | API 엔드포인트 | 2025-11-13 |
| PROJECT_STRUCTURE.md | ~30 | 디렉토리 구조 | 2025-11-13 |

**총 페이지 수**: ~120 페이지

---

## 🔗 외부 링크

### 공식 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Prefect 문서](https://docs.prefect.io/)

### 개발 도구
- [Swagger UI](http://localhost:8000/docs) (로컬)
- [ReDoc](http://localhost:8000/redoc) (로컬)
- [Prefect UI](http://localhost:4200) (로컬)

---

## ✅ 체크리스트

### 신규 개발자
- [ ] PROJECT_OVERVIEW.md 읽기
- [ ] 개발 환경 설정
- [ ] PROJECT_STRUCTURE.md 파악
- [ ] DATABASE_SCHEMA.md 이해
- [ ] 첫 API 호출 성공
- [ ] 첫 코드 커밋

### 문서 업데이트
- [ ] 변경사항 반영
- [ ] 스크린샷 업데이트
- [ ] 예제 코드 검증
- [ ] 링크 확인
- [ ] 최종 업데이트 날짜 수정

---

**마지막 업데이트**: 2025-11-13
**문서 버전**: 1.1.0
**작성자**: 프로젝트 팀
