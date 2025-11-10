# 전처리 및 JSON 생성 전략

## 문제 상황
- ZIP 압축 해제 시 최대 300개 CSV 파일 생성
- 각 파일을 전처리하여 JSON 생성
- JSON 파일을 S3에 업로드
- Document 테이블에 메타정보 저장

## 전략 비교

### 옵션 1: 배치 처리 (한꺼번에)
```
1. 모든 JSON 생성 (300개)
2. 모든 S3 업로드 (300개)
3. 모든 Document 저장 (300개) - 한 번의 commit
```

**장점:**
- ✅ 트랜잭션 효율 (1번의 commit)
- ✅ 빠른 처리 속도
- ✅ 원자성 보장 (전체 성공 또는 전체 실패)

**단점:**
- ❌ 중간 실패 시 전체 롤백 필요
- ❌ 메모리 사용량 증가 (300개 JSON 모두 메모리에)
- ❌ 진행상황 추적 어려움
- ❌ 부분 재시도 불가능
- ❌ 타임아웃 위험 (300개 처리 시간)

---

### 옵션 2: 개별 처리 (1개씩)
```
각 파일마다:
1. JSON 생성
2. S3 업로드
3. Document 저장 (commit)
```

**장점:**
- ✅ 중간 실패 시 부분 재시도 가능
- ✅ 진행상황 추적 용이 (각 파일별 상태 관리)
- ✅ 메모리 효율적
- ✅ 타임아웃 위험 낮음
- ✅ 실패한 파일만 재처리 가능

**단점:**
- ❌ 트랜잭션 오버헤드 (300번 commit)
- ❌ 상대적으로 느림
- ❌ DB 커넥션 부하 증가

---

### 옵션 3: 청크 처리 (예: 50개씩)
```
50개씩 묶어서:
1. JSON 생성 (50개)
2. S3 업로드 (50개)
3. Document 저장 (50개) - 한 번의 commit
```

**장점:**
- ✅ 배치와 개별의 장점 균형
- ✅ 트랜잭션 오버헤드 감소 (6번 commit)
- ✅ 부분 재시도 가능 (청크 단위)
- ✅ 진행상황 추적 가능 (청크 단위)

**단점:**
- ⚠️ 청크 크기 조정 필요
- ⚠️ 청크 중간 실패 시 해당 청크 전체 롤백

---

## 권장 전략: **개별 처리 + 청크 commit**

### 이유
1. **안정성**: 중간 실패 시 부분 재시도 가능
2. **추적 가능성**: 각 파일별 상태 관리로 진행상황 확인 가능
3. **확장성**: 파일 수가 많아져도 안정적
4. **디버깅**: 실패한 파일만 개별적으로 재처리 가능

### 구현 방식

```python
# 개별 처리: JSON 생성 → S3 업로드 → Document 저장
# 청크 commit: 10-50개마다 commit (성능 최적화)

CHUNK_SIZE = 50  # 설정 가능

for idx, unzipped_file in enumerate(unzipped_files):
    try:
        # 1. 전처리 및 JSON 생성
        json_content = preprocess_file(unzipped_file)
        
        # 2. S3 업로드
        s3_path = await upload_json_to_s3(json_content, json_key)
        
        # 3. Document 저장 (메모리에만)
        document = create_document_object(...)
        documents_to_insert.append(document)
        
        # 4. 청크 단위 commit
        if (idx + 1) % CHUNK_SIZE == 0:
            bulk_insert_documents(documents_to_insert)
            documents_to_insert = []
            logger.info(f"진행상황: {idx + 1}/{total} 완료")
            
    except Exception as e:
        # 실패한 파일 기록
        failed_files.append({
            'file': unzipped_file,
            'error': str(e)
        })
        logger.error(f"파일 처리 실패: {unzipped_file}, error: {e}")

# 남은 파일들 commit
if documents_to_insert:
    bulk_insert_documents(documents_to_insert)
```

---

## 구체적 구현 방안

### 방법 1: 개별 처리 (권장)
```python
async def preprocess_and_create_json(
    self, program_id, user_id, unzipped_files, ...
):
    """JSON 생성 → S3 업로드 → Document 저장을 개별 처리"""
    
    document_crud = DocumentCRUD(self.db)
    CHUNK_COMMIT_SIZE = 50  # 50개마다 commit
    
    documents_batch = []
    
    for idx, unzipped_file_path in enumerate(unzipped_files):
        try:
            # 1. 전처리 및 JSON 생성
            json_content = await self._preprocess_file(unzipped_file_path, ...)
            
            # 2. JSON 파일 생성 및 S3 업로드
            json_filename = f"processed_{program_id}_{idx}.json"
            json_s3_key = f"programs/{program_id}/processed/{json_filename}"
            json_s3_path = await self._upload_json_to_s3(
                json_content=json_content,
                s3_key=json_s3_key
            )
            
            # 3. Document 객체 생성 (메모리에만)
            document_id = gen()
            document_data = {
                'document_id': document_id,
                'document_name': f"{program_title}_{json_filename}",
                'original_filename': json_filename,
                'file_key': json_s3_key,
                'file_size': len(json_content.encode('utf-8')),
                'file_type': 'application/json',
                'file_extension': 'json',
                'user_id': user_id,
                'upload_path': json_s3_path,
                'status': 'processing',
                'metadata_json': {
                    'program_id': program_id,
                    'processing_stage': 'preprocessed',
                }
            }
            documents_batch.append(document_data)
            
            # 4. 청크 단위 commit
            if (idx + 1) % CHUNK_COMMIT_SIZE == 0:
                await self._bulk_insert_documents(document_crud, documents_batch)
                documents_batch = []
                logger.info(f"진행상황: {idx + 1}/{len(unzipped_files)} 완료")
                
        except Exception as e:
            logger.error(f"파일 처리 실패: {unzipped_file_path}, error: {e}")
            # 실패한 파일은 건너뛰고 계속 진행
            continue
    
    # 남은 파일들 commit
    if documents_batch:
        await self._bulk_insert_documents(document_crud, documents_batch)
    
    return processed_json_files
```

### 방법 2: 완전 개별 처리 (더 안전)
```python
async def preprocess_and_create_json(...):
    """JSON 생성 → S3 업로드 → Document 저장을 완전 개별 처리"""
    
    document_crud = DocumentCRUD(self.db)
    
    for idx, unzipped_file_path in enumerate(unzipped_files):
        try:
            # 1. 전처리 및 JSON 생성
            json_content = await self._preprocess_file(...)
            
            # 2. S3 업로드
            json_s3_path = await self._upload_json_to_s3(...)
            
            # 3. Document 저장 및 즉시 commit
            document_crud.create_document(...)
            self.db.commit()
            
            logger.info(f"진행상황: {idx + 1}/{len(unzipped_files)} 완료")
            
        except Exception as e:
            logger.error(f"파일 처리 실패: {unzipped_file_path}, error: {e}")
            self.db.rollback()
            # 실패한 파일 기록
            failed_files.append(unzipped_file_path)
            continue
```

---

## 성능 비교 (예상)

| 방식 | 300개 처리 시간 | DB commit 횟수 | 메모리 사용 | 안정성 |
|------|---------------|---------------|------------|--------|
| 배치 처리 | ~5분 | 1회 | 높음 | 낮음 |
| 개별 처리 | ~8분 | 300회 | 낮음 | 높음 |
| 청크 처리 (50개) | ~6분 | 6회 | 중간 | 중간 |
| **개별 + 청크 commit (50개)** | **~6분** | **6회** | **낮음** | **높음** |

---

## 최종 권장사항

### ✅ **개별 처리 + 청크 commit 방식**

**구현 단계:**
1. JSON 생성 → S3 업로드 → Document 객체 생성 (메모리에)
2. 50개마다 bulk insert 및 commit
3. 실패한 파일은 별도로 기록하여 재시도 가능

**장점:**
- 안정성: 부분 실패 시에도 진행 가능
- 성능: 청크 commit으로 트랜잭션 오버헤드 감소
- 추적: 진행상황 로깅 가능
- 재시도: 실패한 파일만 개별 재처리 가능

**주의사항:**
- 청크 크기는 시스템 부하에 따라 조정 (10-100개)
- 실패한 파일 목록을 별도로 관리하여 재시도 로직 구현
- 진행상황을 Program 테이블의 metadata_json에 저장 가능

