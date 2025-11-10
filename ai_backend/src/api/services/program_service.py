# _*_ coding: utf-8 _*_
"""Program Service for handling program registration and management."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session
from src.api.services.program_uploader import ProgramUploader
from src.api.services.program_validator import ProgramValidator
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.uuid_gen import gen

logger = logging.getLogger(__name__)


class ProgramService:
    """프로그램 관리 서비스"""

    def __init__(self, db: Session, uploader: ProgramUploader = None):
        """
        Args:
            db: 데이터베이스 세션
            uploader: ProgramUploader 인스턴스
        """
        self.db = db
        self.validator = ProgramValidator()
        self.uploader = uploader or ProgramUploader()
        from src.database.crud.program_crud import ProgramCRUD

        self.program_crud = ProgramCRUD(db)

    def get_program_id_from_plc_id(self, plc_id: str) -> Optional[str]:
        """PLC ID로 매핑된 program_id 조회"""
        if not plc_id:
            return None

        try:
            from shared_core import PLCCRUD

            plc_crud = PLCCRUD(self.db)
            plc = plc_crud.get_plc_by_plc_id(plc_id)
            if plc and plc.program_id:
                program_id = plc.program_id
                logger.info("PLC %s의 program_id 조회: %s", plc_id, program_id)
                return program_id
            else:
                logger.warning(
                    "PLC %s를 찾을 수 없거나 program_id가 없습니다.",
                    plc_id,
                )
                return None
        except Exception as e:
            logger.error("PLC %s의 program_id 조회 실패: %s", plc_id, str(e))
            return None

    async def register_program(
        self,
        program_title: str,
        program_description: Optional[str],
        user_id: str,
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
    ) -> Dict:
        """
        프로그램 등록 (유효성 검사 + 비동기 처리)

        Returns:
            Dict: 프로그램 등록 결과
        """
        try:
            # 프로그램 ID 생성
            program_id = gen()

            # 1. 유효성 검사 (동기)
            logger.info(f"프로그램 유효성 검사 시작: program_id={program_id}")
            is_valid, errors, warnings, checked_files = self.validator.validate_files(
                ladder_zip=ladder_zip,
                classification_xlsx=classification_xlsx,
                device_comment_csv=device_comment_csv,
            )

            # 검증 실패 시 즉시 응답 반환 (DB 저장하지 않음)
            if not is_valid:
                return {
                    "program_id": program_id,
                    "status": "validation_failed",
                    "is_valid": False,
                    "errors": errors,
                    "warnings": warnings,
                    "checked_files": checked_files,
                    "message": "유효성 검사를 통과하지 못했습니다.",
                }

            # 2. 유효성 검사 통과 → RDB에 메타정보 저장 (동기)
            logger.info(f"프로그램 메타데이터 저장 시작: program_id={program_id}")
            from shared_core import Program

            self.program_crud.create_program(
                program_id=program_id,
                program_title=program_title,
                program_description=program_description,
                user_id=user_id,
                status=Program.STATUS_PROCESSING,  # 검증 통과 후 processing
            )
            self.db.commit()
            logger.info(f"프로그램 메타데이터 저장 완료: program_id={program_id}")

            # 3. 비동기 처리 시작 (백그라운드 태스크)
            # - S3 업로드 및 압축 해제
            # - DB에 S3 경로 저장
            # - Vector DB 인덱싱
            asyncio.create_task(
                self._process_program_async(
                    program_id=program_id,
                    program_title=program_title,
                    user_id=user_id,
                    ladder_zip=ladder_zip,
                    classification_xlsx=classification_xlsx,
                    device_comment_csv=device_comment_csv,
                )
            )

            # 4. 즉시 응답 반환 (ProgramUploadResponse)
            return {
                "program_id": program_id,
                "program_title": program_title,
                "status": "processing",
                "is_valid": True,
                "errors": [],
                "warnings": warnings,
                "checked_files": checked_files,
                "message": "유효성 검사를 통과했습니다. 파일 처리가 진행 중입니다.",
            }

        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 등록 중 오류: {str(e)}")
            raise HandledException(ResponseCode.PROGRAM_REGISTRATION_ERROR, e=e)

    async def _process_program_async(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
    ):
        """
        비동기로 프로그램 처리 (S3 업로드, DB 저장, Vector DB 인덱싱)
        """
        try:
            logger.info(f"비동기 프로그램 처리 시작: program_id={program_id}")

            # 1. S3에 파일 업로드 및 ZIP 압축 해제 (비동기)
            logger.info(f"S3 업로드 시작: program_id={program_id}")
            s3_paths = await self.uploader.upload_and_unzip(
                ladder_zip=ladder_zip,
                classification_xlsx=classification_xlsx,
                device_comment_csv=device_comment_csv,
                program_id=program_id,
                user_id=user_id,
            )
            logger.info(f"S3 업로드 완료: program_id={program_id}")

            # 2. DB에 상세 데이터 저장 (비동기)
            logger.info(f"DB 저장 시작: program_id={program_id}")
            self.program_crud.update_program_s3_paths(
                program_id=program_id, s3_paths=s3_paths
            )
            self.db.commit()
            logger.info(f"DB 저장 완료: program_id={program_id}")

            # 3. 전처리: ZIP 압축 해제 파일들로 JSON 생성 및 S3 업로드
            logger.info(f"전처리 시작: program_id={program_id}")
            unzipped_files = s3_paths.get("unzipped_files", [])

            preprocess_result = await self.uploader.preprocess_and_create_json(
                program_id=program_id,
                user_id=user_id,
                unzipped_files=unzipped_files,
                classification_xlsx_path=s3_paths.get("classification_xlsx_path"),
                device_comment_csv_path=s3_paths.get("device_comment_csv_path"),
            )

            processed_json_files = preprocess_result.get("processed_files", {})
            failed_preprocess_files = preprocess_result.get("failed_files", [])
            preprocess_summary = preprocess_result.get("summary", {})

            logger.info(
                f"전처리 완료: {preprocess_summary.get('success', 0)}개 성공, "
                f"{preprocess_summary.get('failed', 0)}개 실패"
            )

            # 전처리 실패 정보를 ProcessingFailure 테이블에 저장
            from src.database.crud.processing_failure_crud import ProcessingFailureCRUD

            from shared_core import ProcessingFailure

            failure_crud = ProcessingFailureCRUD(self.db)
            for failed_file in failed_preprocess_files:
                failure_id = gen()
                failure_crud.create_failure(
                    failure_id=failure_id,
                    program_id=program_id,
                    failure_type=ProcessingFailure.FAILURE_TYPE_PREPROCESSING,
                    error_message=failed_file.get("error", "전처리 실패"),
                    file_path=failed_file.get("file_path"),
                    file_index=failed_file.get("index"),
                    error_details=failed_file,
                )
            if failed_preprocess_files:
                self.db.commit()
                logger.info(f"전처리 실패 정보 저장: {len(failed_preprocess_files)}개")

            # 4. 전처리된 JSON 파일들을 Document 테이블에 저장 (청크 단위)
            logger.info(f"Document 테이블 저장 시작: program_id={program_id}")
            from src.database.crud.document_crud import DocumentCRUD
            from src.database.crud.processing_failure_crud import ProcessingFailureCRUD

            from shared_core import ProcessingFailure

            document_crud = DocumentCRUD(self.db)
            failure_crud = ProcessingFailureCRUD(self.db)
            created_documents = []
            failed_document_files = []
            CHUNK_COMMIT_SIZE = 50  # 50개마다 commit
            total_files = len(processed_json_files)

            for idx, (json_key, json_info) in enumerate(
                processed_json_files.items(), start=1
            ):
                try:
                    document_id = gen()

                    # Document 테이블에 저장
                    document_crud.create_document(
                        document_id=document_id,
                        document_name=f"{program_title}_{json_info['filename']}",
                        original_filename=json_info["filename"],
                        file_key=json_info["s3_key"],
                        file_size=json_info.get(
                            "file_size", 0
                        ),  # 전처리에서 계산된 파일 크기
                        file_type="application/json",
                        file_extension="json",
                        user_id=user_id,
                        upload_path=json_info["s3_path"],
                        status="processing",
                        document_type="common",
                        metadata_json={
                            "program_id": program_id,
                            "program_title": program_title,
                            "source_file": json_key,
                            "processing_stage": "preprocessed",
                            "json_filename": json_info["filename"],
                        },
                    )

                    created_documents.append(
                        {
                            "document_id": document_id,
                            "s3_path": json_info["s3_path"],
                            "filename": json_info["filename"],
                        }
                    )

                    # 청크 단위 commit (성능 최적화)
                    if idx % CHUNK_COMMIT_SIZE == 0:
                        self.db.commit()
                        logger.info(
                            f"Document 저장 진행상황: {idx}/{total_files} "
                            f"완료 (청크 commit)"
                        )

                except Exception as doc_error:
                    logger.error(
                        f"Document 생성 실패: {json_info.get('filename')}, "
                        f"error: {str(doc_error)}"
                    )
                    self.db.rollback()

                    # 실패 정보를 ProcessingFailure 테이블에 저장
                    failure_id = gen()
                    failure_crud.create_failure(
                        failure_id=failure_id,
                        program_id=program_id,
                        failure_type=ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE,
                        error_message=str(doc_error),
                        filename=json_info.get("filename"),
                        s3_path=json_info.get("s3_path"),
                        s3_key=json_info.get("s3_key"),
                        file_path=json_info.get("source_file_path"),
                        file_index=json_info.get("source_index"),
                        error_details={
                            "json_key": json_key,
                            "source_file_path": json_info.get("source_file_path"),
                            "source_index": json_info.get("source_index"),
                        },
                    )
                    self.db.commit()

                    # 실패한 파일 정보 기록 (메모리)
                    failed_document_files.append(
                        {
                            "json_key": json_key,
                            "filename": json_info.get("filename"),
                            "s3_path": json_info.get("s3_path"),
                            "source_file_path": json_info.get("source_file_path"),
                            "source_index": json_info.get("source_index"),
                            "error": str(doc_error),
                            "failure_id": failure_id,
                        }
                    )
                    # 실패해도 계속 진행
                    continue

            # 남은 파일들 commit
            if total_files % CHUNK_COMMIT_SIZE != 0:
                self.db.commit()

            document_summary = {
                "total": total_files,
                "success": len(created_documents),
                "failed": len(failed_document_files),
            }

            logger.info(
                f"Document 테이블 저장 완료: {document_summary['success']}개 성공, "
                f"{document_summary['failed']}개 실패"
            )

            # 부분 실패가 있는 경우 경고 로깅
            has_partial_failure = (
                len(failed_preprocess_files) > 0 or len(failed_document_files) > 0
            )

            if has_partial_failure:
                logger.warning(
                    f"부분 실패 발생: program_id={program_id}, "
                    f"전처리 실패: {len(failed_preprocess_files)}개, "
                    f"Document 저장 실패: {len(failed_document_files)}개"
                )

            # 실패 정보 요약을 Program.metadata_json에 저장 (통계용)
            processing_metadata = {
                "total_expected": len(unzipped_files),
                "total_successful_documents": len(created_documents),
                "has_partial_failure": has_partial_failure,
                "preprocessing_summary": preprocess_summary,
                "document_storage_summary": document_summary,
                # 실제 실패 정보는 ProcessingFailure 테이블에서 조회
            }

            # Program.metadata_json 업데이트 (통계만)
            from shared_core import Program

            program = self.program_crud.get_program(program_id)
            if program:
                current_metadata = program.metadata_json or {}
                current_metadata.update(processing_metadata)
                self.program_crud.update_program(
                    program_id=program_id, metadata_json=current_metadata
                )
                self.db.commit()
                logger.info(f"처리 메타데이터 저장 완료: program_id={program_id}")

            # 5. Vector DB 인덱싱 요청 (비동기)
            logger.info(f"Vector DB 인덱싱 요청 시작: program_id={program_id}")

            # ProcessingJob 테이블에 인덱싱 작업 생성
            from shared_core import ProcessingJobCRUD

            job_crud = ProcessingJobCRUD(self.db)
            job_id = (
                f"vector_indexing_{program_id}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 인덱싱 작업 생성
            job_crud.create_job(
                job_id=job_id,
                doc_id=program_id,  # program_id를 doc_id로 사용
                job_type="vector_indexing",
                total_steps=1,
            )
            self.db.commit()
            logger.info(f"Vector DB 인덱싱 작업 생성: job_id={job_id}")

            try:
                # Vector DB 인덱싱 요청
                indexing_success = await self.uploader.request_vector_indexing(
                    program_id=program_id, s3_paths=s3_paths
                )

                if indexing_success:
                    # 인덱싱 작업 성공 처리
                    job_crud.update_job_status(
                        job_id=job_id,
                        status="completed",
                        completed_steps=1,
                        current_step="Vector DB 인덱싱 완료",
                        result_data={"program_id": program_id, "status": "completed"},
                    )

                    # 프로그램 상태 업데이트
                    self.program_crud.update_program_status(
                        program_id=program_id, status=Program.STATUS_COMPLETED
                    )
                    self.program_crud.update_program_vector_info(
                        program_id=program_id, vector_indexed=True
                    )
                    self.db.commit()
                    logger.info(f"프로그램 처리 완료: program_id={program_id}")
                else:
                    # 인덱싱 작업 실패 처리
                    job_crud.update_job_status(
                        job_id=job_id,
                        status="failed",
                        completed_steps=0,
                        current_step="Vector DB 인덱싱 실패",
                        error_message="Vector DB 인덱싱 요청 실패",
                    )

                    # 프로그램 상태 업데이트
                    self.program_crud.update_program_status(
                        program_id=program_id, status=Program.STATUS_INDEXING_FAILED
                    )
                    self.db.commit()
                    logger.warning(f"Vector DB 인덱싱 실패: program_id={program_id}")

            except Exception as indexing_error:
                # 인덱싱 중 예외 발생 처리
                error_msg = str(indexing_error)
                job_crud.update_job_status(
                    job_id=job_id,
                    status="failed",
                    completed_steps=0,
                    current_step="Vector DB 인덱싱 오류",
                    error_message=error_msg,
                )

                self.program_crud.update_program_status(
                    program_id=program_id, status=Program.STATUS_INDEXING_FAILED
                )
                self.db.commit()
                logger.error(
                    f"Vector DB 인덱싱 중 오류: program_id={program_id}, error={error_msg}"
                )
                raise

        except Exception as e:
            logger.error(
                f"비동기 프로그램 처리 중 오류: program_id={program_id}, error={str(e)}"
            )
            from shared_core import Program

            self.program_crud.update_program_status(
                program_id=program_id,
                status=Program.STATUS_FAILED,
                error_message=str(e),
            )
            self.db.commit()

    async def get_program(self, program_id: str, user_id: str) -> Dict:
        """프로그램 정보 조회"""
        try:
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인
            if program.user_id != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램에 접근할 권한이 없습니다.",
                )

            return {
                "program_id": program.program_id,
                "program_title": program.program_title,
                "program_description": program.program_description,
                "user_id": program.user_id,
                "status": program.status,
                "s3_paths": program.s3_paths,
                "vector_indexed": program.vector_indexed,
                "vector_collection_name": program.vector_collection_name,
                "error_message": program.error_message,
                "created_at": program.created_at,
                "updated_at": program.updated_at,
                "processed_at": program.processed_at,
            }
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 조회 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def get_user_programs(self, user_id: str) -> List[Dict]:
        """사용자의 프로그램 목록 조회"""
        try:
            programs = self.program_crud.get_user_programs(user_id)
            return [
                {
                    "program_id": program.program_id,
                    "program_title": program.program_title,
                    "program_description": program.program_description,
                    "user_id": program.user_id,
                    "status": program.status,
                    "s3_paths": program.s3_paths,
                    "vector_indexed": program.vector_indexed,
                    "vector_collection_name": program.vector_collection_name,
                    "error_message": program.error_message,
                    "created_at": program.created_at,
                    "updated_at": program.updated_at,
                    "processed_at": program.processed_at,
                }
                for program in programs
            ]
        except Exception as e:
            logger.error(f"사용자 프로그램 목록 조회 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def retry_failed_files(
        self, program_id: str, user_id: str, retry_type: str = "all"
    ) -> Dict:
        """
        실패한 파일 재시도

        Args:
            program_id: 프로그램 ID
            user_id: 사용자 ID
            retry_type: 재시도 타입 ("preprocessing", "document", "all")

        Returns:
            Dict: 재시도 결과
        """
        try:
            # 프로그램 정보 조회
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인
            if program.user_id != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램에 접근할 권한이 없습니다.",
                )

            # 실패 정보 조회 (ProcessingFailure 테이블에서)
            from src.database.crud.processing_failure_crud import ProcessingFailureCRUD

            from shared_core import ProcessingFailure

            failure_crud = ProcessingFailureCRUD(self.db)

            # 재시도 대상 실패 정보 조회
            failure_type_filter = None
            if retry_type == "preprocessing":
                failure_type_filter = ProcessingFailure.FAILURE_TYPE_PREPROCESSING
            elif retry_type == "document":
                failure_type_filter = ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE

            pending_failures = failure_crud.get_program_failures(
                program_id=program_id,
                failure_type=failure_type_filter,
                status=ProcessingFailure.STATUS_PENDING,
            )

            retry_results = {
                "preprocessing": {"retried": 0, "success": 0, "failed": 0},
                "document": {"retried": 0, "success": 0, "failed": 0},
            }

            # 실패 파일 재시도
            for failure in pending_failures:
                try:
                    # 재시도 횟수 증가
                    failure_crud.increment_retry_count(failure.failure_id)
                    failure_crud.update_failure_status(
                        failure_id=failure.failure_id,
                        status=ProcessingFailure.STATUS_RETRYING,
                    )

                    if (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_PREPROCESSING
                    ):
                        retry_results["preprocessing"]["retried"] += 1
                        # TODO: 전처리 재시도 로직 구현
                        # 재시도 성공 시
                        # failure_crud.mark_as_resolved(
                        #     failure_id=failure.failure_id, resolved_by="manual"
                        # )
                        # retry_results["preprocessing"]["success"] += 1

                    elif (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE
                    ):
                        retry_results["document"]["retried"] += 1

                        # Document 재생성
                        from src.database.crud.document_crud import DocumentCRUD
                        from src.utils.uuid_gen import gen

                        document_crud = DocumentCRUD(self.db)
                        document_id = gen()

                        document_crud.create_document(
                            document_id=document_id,
                            document_name=f"{program.program_title}_{failure.filename}",
                            original_filename=failure.filename,
                            file_key=failure.s3_key,
                            file_size=0,
                            file_type="application/json",
                            file_extension="json",
                            user_id=user_id,
                            upload_path=failure.s3_path,
                            status="processing",
                            document_type="common",
                            metadata_json={
                                "program_id": program_id,
                                "program_title": program.program_title,
                                "processing_stage": "preprocessed",
                                "retry_count": failure.retry_count,
                                "is_retry": True,
                                "failure_id": failure.failure_id,
                            },
                        )
                        self.db.commit()

                        # 재시도 성공
                        failure_crud.mark_as_resolved(
                            failure_id=failure.failure_id, resolved_by="manual"
                        )
                        retry_results["document"]["success"] += 1
                        logger.info(
                            f"Document 재생성 성공: failure_id={failure.failure_id}, "
                            f"filename={failure.filename}"
                        )

                except Exception as e:
                    # 재시도 실패
                    if (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_PREPROCESSING
                    ):
                        retry_results["preprocessing"]["failed"] += 1
                    elif (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE
                    ):
                        retry_results["document"]["failed"] += 1

                    failure_crud.update_failure_status(
                        failure_id=failure.failure_id,
                        status=ProcessingFailure.STATUS_PENDING,
                        error_message=str(e),
                    )
                    self.db.rollback()
                    logger.error(
                        f"재시도 실패: failure_id={failure.failure_id}, "
                        f"error: {str(e)}"
                    )
                    continue

            # 재시도 이력 저장 (통계용)
            if (
                retry_results["preprocessing"]["retried"] > 0
                or retry_results["document"]["retried"] > 0
            ):
                program = self.program_crud.get_program(program_id)
                if program:
                    current_metadata = program.metadata_json or {}
                    retry_history = current_metadata.get("retry_history", [])
                    retry_history.append(
                        {
                            "retry_type": retry_type,
                            "timestamp": datetime.now().isoformat(),
                            "results": retry_results,
                        }
                    )
                    current_metadata["retry_history"] = retry_history
                    self.program_crud.update_program(
                        program_id=program_id, metadata_json=current_metadata
                    )
                    self.db.commit()

            return {
                "program_id": program_id,
                "retry_type": retry_type,
                "results": retry_results,
                "message": "재시도 완료",
            }

        except HandledException:
            raise
        except Exception as e:
            logger.error(f"재시도 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def get_program_failures(
        self, program_id: str, user_id: str, failure_type: Optional[str] = None
    ) -> List[Dict]:
        """프로그램의 실패 정보 목록 조회"""
        try:
            # 프로그램 정보 조회
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인
            if program.user_id != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램에 접근할 권한이 없습니다.",
                )

            # 실패 정보 조회
            from src.database.crud.processing_failure_crud import ProcessingFailureCRUD

            failure_crud = ProcessingFailureCRUD(self.db)
            failures = failure_crud.get_program_failures(
                program_id=program_id, failure_type=failure_type
            )

            return [
                {
                    "failure_id": failure.failure_id,
                    "program_id": failure.program_id,
                    "failure_type": failure.failure_type,
                    "file_path": failure.file_path,
                    "file_index": failure.file_index,
                    "filename": failure.filename,
                    "s3_path": failure.s3_path,
                    "s3_key": failure.s3_key,
                    "error_message": failure.error_message,
                    "error_details": failure.error_details,
                    "retry_count": failure.retry_count,
                    "max_retry_count": failure.max_retry_count,
                    "status": failure.status,
                    "resolved_at": (
                        failure.resolved_at.isoformat() if failure.resolved_at else None
                    ),
                    "last_retry_at": (
                        failure.last_retry_at.isoformat()
                        if failure.last_retry_at
                        else None
                    ),
                    "resolved_by": failure.resolved_by,
                    "created_at": failure.created_at.isoformat(),
                    "updated_at": (
                        failure.updated_at.isoformat() if failure.updated_at else None
                    ),
                }
                for failure in failures
            ]
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"실패 정보 조회 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
