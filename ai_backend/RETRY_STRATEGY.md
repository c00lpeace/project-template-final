# 재처리 전략 및 방법

## 개요

실패한 파일을 재처리하는 방법은 여러 가지가 있습니다. 각 방법의 장단점과 구현 방안을 정리했습니다.

## 재처리 방법 비교

### 1. 수동 재시도 API (현재 구현)

**구현 방식:**
- 사용자가 API를 호출하여 재시도
- `POST /api/v1/programs/{program_id}/retry`

**장점:**
- ✅ 즉시 실행 가능
- ✅ 사용자가 재시도 시점 제어
- ✅ 구현이 간단

**단점:**
- ❌ 사용자가 수동으로 호출해야 함
- ❌ 실패를 자동으로 감지하지 못함

---

### 2. 스케줄링 기반 재처리 (권장)

#### 방법 A: APScheduler (Python 내장)

**구현 방식:**
- FastAPI 시작 시 백그라운드 스케줄러 시작
- 주기적으로 실패한 파일을 찾아서 재처리

**장점:**
- ✅ 자동으로 주기적 재시도
- ✅ 별도 서비스 불필요
- ✅ FastAPI와 통합 용이

**단점:**
- ⚠️ 단일 인스턴스에서만 동작 (멀티 인스턴스 시 중복 실행 위험)

**구현 예시:**
```python
# ai_backend/src/scheduler/retry_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

class RetryScheduler:
    def __init__(self, program_service):
        self.scheduler = AsyncIOScheduler()
        self.program_service = program_service
    
    def start(self):
        # 매 1시간마다 실행
        self.scheduler.add_job(
            self.retry_failed_programs,
            CronTrigger(minute=0),  # 매시간 정각
            id='retry_failed_programs',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("재시도 스케줄러 시작")
    
    async def retry_failed_programs(self):
        """실패한 파일이 있는 프로그램 찾아서 재시도"""
        # DB에서 has_partial_failure=True인 프로그램 조회
        # 각 프로그램에 대해 retry_failed_files() 호출
        pass
```

#### 방법 B: Prefect Schedules (프로젝트에 이미 사용 중)

**구현 방식:**
- Prefect Flow로 재처리 작업 정의
- Prefect Scheduler로 주기적 실행

**장점:**
- ✅ 이미 Prefect 인프라 존재
- ✅ 웹 UI로 모니터링 가능
- ✅ 재시도 정책 설정 가능

**단점:**
- ⚠️ Prefect 서버 필요

**구현 예시:**
```python
# doc_processor/flow/retry_failed_files_flow.py
from prefect import flow, task
from prefect.schedules import CronSchedule

schedule = CronSchedule(cron="0 * * * *", timezone="Asia/Seoul")

@flow(name="retry_failed_files", schedule=schedule)
async def retry_failed_files_flow():
    """매시간 실패한 파일 재처리"""
    # DB에서 실패한 프로그램 조회 및 재시도
    pass
```

#### 방법 C: Kubernetes CronJob

**구현 방식:**
- Kubernetes CronJob으로 재처리 스크립트 주기적 실행

**장점:**
- ✅ 분산 환경에서 안전
- ✅ 인프라 레벨에서 관리

**단점:**
- ⚠️ Kubernetes 환경 필요

---

### 3. 자동 재시도 (실패 감지 시 즉시)

**구현 방식:**
- 처리 완료 후 자동으로 실패 파일 체크
- 실패가 있으면 자동으로 재시도

**장점:**
- ✅ 즉시 재시도
- ✅ 사용자 개입 불필요

**단점:**
- ❌ 일시적 오류 시 즉시 재시도는 비효율적
- ❌ 재시도 횟수 제한 필요

**구현 예시:**
```python
# _process_program_async() 끝부분에 추가
async def _process_program_async(...):
    # ... 기존 처리 로직 ...
    
    # 처리 완료 후 실패 파일 자동 재시도
    metadata = program.metadata_json or {}
    if metadata.get("has_partial_failure"):
        # 자동 재시도 (최대 3회)
        retry_count = metadata.get("auto_retry_count", 0)
        if retry_count < 3:
            await self._auto_retry_failed_files(program_id, user_id)
```

---

### 4. 백그라운드 워커 (큐 기반)

#### 방법 A: Celery + Redis/RabbitMQ

**구현 방식:**
- 실패한 파일을 큐에 넣기
- Celery Worker가 큐에서 꺼내서 재처리

**장점:**
- ✅ 분산 처리 가능
- ✅ 재시도 정책 설정 가능 (exponential backoff)
- ✅ 우선순위 큐 지원

**단점:**
- ⚠️ 추가 인프라 필요 (Redis/RabbitMQ)

**구현 예시:**
```python
# celery_tasks.py
from celery import Celery

celery_app = Celery('retry_tasks')

@celery_app.task(bind=True, max_retries=3)
def retry_failed_file(self, program_id, failed_file):
    try:
        # 재처리 로직
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)  # 60초 후 재시도
```

#### 방법 B: asyncio + Redis Queue (현재 프로젝트 스타일)

**구현 방식:**
- Redis Queue에 실패한 파일 정보 저장
- 백그라운드 워커가 주기적으로 큐에서 가져와 처리

**장점:**
- ✅ 현재 프로젝트와 일관성
- ✅ Redis 이미 사용 중일 가능성

**단점:**
- ⚠️ 직접 구현 필요

---

### 5. 이벤트 기반 재시도

**구현 방식:**
- 처리 완료 이벤트 발생 시 실패 체크
- 실패가 있으면 재시도 태스크 생성

**장점:**
- ✅ 즉각적인 반응
- ✅ 이벤트 기반 아키텍처와 일관성

**단점:**
- ⚠️ 이벤트 시스템 구축 필요

---

## 권장 방법: **하이브리드 접근**

### 1단계: 즉시 재시도 (자동)
- 처리 완료 후 일시적 오류만 즉시 재시도 (최대 1회)
- 재시도 간격: 5-10초

### 2단계: 스케줄링 재시도 (자동)
- 매시간 또는 매일 주기적으로 실패한 파일 재시도
- APScheduler 또는 Prefect Schedules 사용

### 3단계: 수동 재시도 (사용자)
- 스케줄링으로도 해결 안 될 때 사용자가 수동 호출

---

## 구현 예시: APScheduler 기반

### 1. 스케줄러 모듈 생성

```python
# ai_backend/src/scheduler/retry_scheduler.py
import logging
from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RetryScheduler:
    """실패한 파일 재처리 스케줄러"""

    def __init__(self, db_session_getter, program_service_getter):
        """
        Args:
            db_session_getter: DB 세션을 반환하는 함수
            program_service_getter: ProgramService를 반환하는 함수
        """
        self.scheduler = AsyncIOScheduler()
        self.db_session_getter = db_session_getter
        self.program_service_getter = program_service_getter

    def start(self):
        """스케줄러 시작"""
        # 매시간 정각에 실행
        self.scheduler.add_job(
            self.retry_failed_programs,
            CronTrigger(minute=0),  # 매시간 정각
            id="retry_failed_programs",
            replace_existing=True,
            max_instances=1,  # 동시 실행 방지
        )

        # 매일 새벽 2시에 실행
        self.scheduler.add_job(
            self.retry_failed_programs,
            CronTrigger(hour=2, minute=0),  # 매일 새벽 2시
            id="retry_failed_programs_daily",
            replace_existing=True,
            max_instances=1,
        )

        self.scheduler.start()
        logger.info("재시도 스케줄러 시작")

    def shutdown(self):
        """스케줄러 종료"""
        self.scheduler.shutdown()
        logger.info("재시도 스케줄러 종료")

    async def retry_failed_programs(self):
        """실패한 파일이 있는 프로그램 찾아서 재시도"""
        try:
            logger.info("스케줄된 재시도 시작")

            # DB 세션 및 서비스 가져오기
            db = self.db_session_getter()
            program_service = self.program_service_getter()

            # 실패한 파일이 있는 프로그램 조회
            from shared_core import Program

            programs_with_failures = (
                db.query(Program)
                .filter(Program.is_deleted == False)
                .filter(Program.status.in_(["processing", "completed"]))
                .all()
            )

            retry_count = 0
            for program in programs_with_failures:
                metadata = program.metadata_json or {}
                if metadata.get("has_partial_failure"):
                    try:
                        # 재시도 실행
                        result = await program_service.retry_failed_files(
                            program_id=program.program_id,
                            user_id=program.user_id,
                            retry_type="all",
                        )

                        retry_count += 1
                        logger.info(
                            f"재시도 완료: program_id={program.program_id}, "
                            f"result={result['results']}"
                        )

                    except Exception as e:
                        logger.error(
                            f"재시도 실패: program_id={program.program_id}, "
                            f"error={str(e)}"
                        )

            logger.info(f"스케줄된 재시도 완료: {retry_count}개 프로그램 처리")

        except Exception as e:
            logger.error(f"스케줄된 재시도 중 오류: {str(e)}")
```

### 2. FastAPI 시작 시 스케줄러 시작

```python
# ai_backend/src/main.py
from src.scheduler.retry_scheduler import RetryScheduler

@app.on_event("startup")
async def startup_event():
    # 스케줄러 시작
    retry_scheduler = RetryScheduler(
        db_session_getter=get_db,
        program_service_getter=get_program_service,
    )
    retry_scheduler.start()
    app.state.retry_scheduler = retry_scheduler

@app.on_event("shutdown")
async def shutdown_event():
    # 스케줄러 종료
    if hasattr(app.state, "retry_scheduler"):
        app.state.retry_scheduler.shutdown()
```

### 3. requirements.txt에 추가

```
APScheduler>=3.10.0
```

---

## 재시도 정책 예시

### 1. Exponential Backoff
```python
retry_delays = [60, 300, 900, 3600]  # 1분, 5분, 15분, 1시간
```

### 2. 최대 재시도 횟수
```python
MAX_RETRY_COUNT = 3
```

### 3. 재시도 조건
- 일시적 오류 (네트워크, 타임아웃): 재시도
- 영구적 오류 (파일 포맷 오류): 재시도 안 함

---

## 모니터링

### 1. 재시도 통계
```python
{
    "total_retries": 100,
    "successful_retries": 85,
    "failed_retries": 15,
    "retry_success_rate": 0.85
}
```

### 2. 알림
- 재시도 실패율이 높을 때 알림
- 특정 프로그램의 재시도가 계속 실패할 때 알림

---

## 권장 구현 순서

1. **1단계**: 수동 재시도 API (현재 구현 완료 ✅)
2. **2단계**: 자동 재시도 (처리 완료 후 즉시, 최대 1회)
3. **3단계**: 스케줄링 재시도 (APScheduler 또는 Prefect)
4. **4단계**: 모니터링 및 알림

