# _*_ coding: utf-8 _*_
"""Program upload module for S3 upload and file processing."""
import io
import logging
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from fastapi import UploadFile

logger = logging.getLogger(__name__)


class ProgramUploader:
    """프로그램 파일 S3 업로드 및 처리 클래스"""

    def __init__(self, s3_client=None, s3_bucket: str = None):
        """
        Args:
            s3_client: S3 클라이언트 (boto3 등)
            s3_bucket: S3 버킷 이름
        """
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket
        # TODO: S3 클라이언트 초기화 로직 추가

    async def upload_and_unzip(
        self,
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
        program_id: str,
        user_id: str,
    ) -> Dict[str, str]:
        """
        파일들을 S3에 업로드하고 ZIP 파일을 압축 해제

        Returns:
            Dict[str, str]: 업로드된 파일들의 S3 경로 정보
                {
                    'ladder_zip_path': 's3://...',
                    'unzipped_base_path': 's3://...',
                    'classification_xlsx_path': 's3://...',
                    'device_comment_csv_path': 's3://...'
                }
        """
        try:
            # 임시 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 1. ZIP 파일 S3 업로드
                ladder_zip.file.seek(0)
                ladder_zip_path = await self._upload_to_s3(
                    file=ladder_zip,
                    s3_key=f"programs/{program_id}/ladder_logic.zip",
                    content_type="application/zip",
                )

                # 2. ZIP 파일 압축 해제
                ladder_zip.file.seek(0)
                unzipped_files = await self._unzip_to_s3(
                    zip_file=ladder_zip,
                    s3_prefix=f"programs/{program_id}/unzipped/",
                    temp_dir=temp_path,
                )

                # 3. XLSX 파일 S3 업로드
                classification_xlsx.file.seek(0)
                classification_xlsx_path = await self._upload_to_s3(
                    file=classification_xlsx,
                    s3_key=f"programs/{program_id}/classification.xlsx",
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

                # 4. CSV 파일 S3 업로드
                device_comment_csv.file.seek(0)
                device_comment_csv_path = await self._upload_to_s3(
                    file=device_comment_csv,
                    s3_key=f"programs/{program_id}/device_comment.csv",
                    content_type="text/csv",
                )

                return {
                    "ladder_zip_path": ladder_zip_path,
                    "unzipped_base_path": f"programs/{program_id}/unzipped/",
                    "unzipped_files": unzipped_files,
                    "classification_xlsx_path": classification_xlsx_path,
                    "device_comment_csv_path": device_comment_csv_path,
                }

        except Exception as e:
            logger.error(f"S3 업로드 및 압축 해제 중 오류: {str(e)}")
            raise

    async def _upload_to_s3(
        self, file: UploadFile, s3_key: str, content_type: str
    ) -> str:
        """
        파일을 S3에 업로드

        Returns:
            str: S3 경로 (s3://bucket/key 형식)
        """
        try:
            file.file.seek(0)
            file_content = file.file.read()
            file.file.seek(0)

            # TODO: S3 업로드 로직 구현
            # 예시:
            # self.s3_client.put_object(
            #     Bucket=self.s3_bucket,
            #     Key=s3_key,
            #     Body=file_content,
            #     ContentType=content_type
            # )

            logger.info(f"S3 업로드 완료: {s3_key}")
            return f"s3://{self.s3_bucket}/{s3_key}"

        except Exception as e:
            logger.error(f"S3 업로드 실패: {str(e)}")
            raise

    async def _unzip_to_s3(
        self, zip_file: UploadFile, s3_prefix: str, temp_dir: Path
    ) -> list:
        """
        ZIP 파일을 압축 해제하여 S3에 업로드

        Returns:
            list: 업로드된 파일 목록
        """
        try:
            zip_file.file.seek(0)
            zip_content = zip_file.file.read()
            zip_file.file.seek(0)

            uploaded_files = []

            # 임시 디렉토리에 압축 해제
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                zip_ref.extractall(temp_dir)

                # 압축 해제된 파일들을 S3에 업로드
                for root, dirs, files in os.walk(temp_dir):
                    for file_name in files:
                        local_file_path = Path(root) / file_name
                        relative_path = local_file_path.relative_to(temp_dir)
                        s3_key = f"{s3_prefix}{relative_path.as_posix()}"

                        # TODO: 각 파일을 S3에 업로드
                        # with open(local_file_path, 'rb') as f:
                        #     self.s3_client.put_object(
                        #         Bucket=self.s3_bucket,
                        #         Key=s3_key,
                        #         Body=f.read()
                        #     )

                        uploaded_files.append(s3_key)
                        logger.debug(f"압축 해제 파일 S3 업로드: {s3_key}")

            logger.info(f"ZIP 압축 해제 완료: {len(uploaded_files)}개 파일")
            return uploaded_files

        except Exception as e:
            logger.error(f"ZIP 압축 해제 실패: {str(e)}")
            raise

    async def preprocess_and_create_json(
        self,
        program_id: str,
        user_id: str,
        unzipped_files: list,
        classification_xlsx_path: str,
        device_comment_csv_path: str,
        chunk_size: int = 50,
    ) -> Dict[str, Dict]:
        """
        ZIP 압축 해제 파일들을 전처리하여 JSON 파일 생성 및 S3 업로드

        전략: 개별 처리 (JSON 생성 → S3 업로드) + 청크 단위 반환
        - 각 파일을 개별적으로 처리하여 중간 실패 시에도 부분 재시도 가능
        - 청크 단위로 결과 반환하여 Document 저장을 청크 단위로 수행

        Args:
            program_id: 프로그램 ID
            user_id: 사용자 ID
            unzipped_files: 압축 해제된 파일 목록 (S3 경로)
            classification_xlsx_path: 분류 XLSX 파일 S3 경로
            device_comment_csv_path: 디바이스 코멘트 CSV 파일 S3 경로
            chunk_size: 청크 크기 (기본값: 50)

        Returns:
            Dict: 전처리 결과
                {
                    'processed_files': {
                        'json_file_0': {
                            's3_path': 's3://...',
                            's3_key': 'programs/{id}/processed/...',
                            'filename': 'processed_{id}_0.json',
                            'json_content': '...',
                        },
                        ...
                    },
                    'failed_files': [
                        {
                            'file_path': 's3://...',
                            'index': 0,
                            'error': '에러 메시지',
                            'retry_count': 0,
                        },
                        ...
                    ],
                    'summary': {
                        'total': 300,
                        'success': 295,
                        'failed': 5,
                    }
                }
        """
        try:
            logger.info(
                f"전처리 시작: program_id={program_id}, "
                f"unzipped_files={len(unzipped_files)}개, "
                f"chunk_size={chunk_size}"
            )

            # TODO: S3에서 파일 다운로드 및 전처리 로직 구현
            # 1. S3에서 압축 해제된 CSV 파일들 다운로드
            # 2. classification_xlsx 파일 다운로드
            # 3. device_comment_csv 파일 다운로드
            # 4. 전처리 로직 수행 (파일 분석, 변환 등)

            processed_json_files = {}
            failed_files = []

            for idx, unzipped_file_path in enumerate(unzipped_files):
                try:
                    # 1. 전처리 로직 수행
                    # processed_data = await self._preprocess_file(
                    #     unzipped_file_path,
                    #     classification_xlsx_path,
                    #     device_comment_csv_path
                    # )

                    # 2. JSON 파일 생성
                    json_filename = f"processed_{program_id}_{idx}.json"
                    json_s3_key = f"programs/{program_id}/processed/{json_filename}"

                    # TODO: JSON 파일 내용 생성
                    # import json
                    # json_content = json.dumps(
                    #     processed_data, ensure_ascii=False
                    # )

                    # 임시로 목업 (실제 구현 시 제거)
                    json_content = '{"mock": "data"}'

                    # 3. S3에 JSON 파일 업로드
                    json_s3_path = await self._upload_json_to_s3(
                        json_content=json_content, s3_key=json_s3_key
                    )

                    processed_json_files[f"json_file_{idx}"] = {
                        "s3_path": json_s3_path,
                        "s3_key": json_s3_key,
                        "filename": json_filename,
                        "json_content": json_content,  # Document 저장 후 삭제 가능
                        "file_size": len(json_content.encode("utf-8")),
                        "source_file_path": unzipped_file_path,
                        "source_index": idx,
                    }

                    # 진행상황 로깅 (청크 단위)
                    if (idx + 1) % chunk_size == 0:
                        logger.info(
                            f"전처리 진행상황: {idx + 1}/{len(unzipped_files)} "
                            f"완료 ({len(processed_json_files)}개 성공, "
                            f"{len(failed_files)}개 실패)"
                        )

                except Exception as file_error:
                    # 개별 파일 처리 실패 시에도 계속 진행
                    logger.error(
                        f"파일 처리 실패: {unzipped_file_path}, "
                        f"error: {str(file_error)}"
                    )
                    failed_files.append(
                        {
                            "file_path": unzipped_file_path,
                            "index": idx,
                            "error": str(file_error),
                            "retry_count": 0,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    continue

            summary = {
                "total": len(unzipped_files),
                "success": len(processed_json_files),
                "failed": len(failed_files),
            }

            logger.info(
                f"전처리 완료: {summary['success']}개 성공, "
                f"{summary['failed']}개 실패 / 총 {summary['total']}개"
            )

            if failed_files:
                logger.warning(
                    f"실패한 파일 {len(failed_files)}개: "
                    f"{[f['file_path'] for f in failed_files[:5]]}"
                )

            return {
                "processed_files": processed_json_files,
                "failed_files": failed_files,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"전처리 중 오류: {str(e)}")
            raise

    async def _upload_json_to_s3(self, json_content: str, s3_key: str) -> str:
        """
        JSON 파일을 S3에 업로드

        Returns:
            str: S3 경로 (s3://bucket/key 형식)
        """
        try:
            # TODO: S3 업로드 로직 구현
            # self.s3_client.put_object(
            #     Bucket=self.s3_bucket,
            #     Key=s3_key,
            #     Body=json_content.encode('utf-8'),
            #     ContentType='application/json'
            # )

            logger.info(f"JSON 파일 S3 업로드 완료: {s3_key}")
            return f"s3://{self.s3_bucket}/{s3_key}"

        except Exception as e:
            logger.error(f"JSON 파일 S3 업로드 실패: {str(e)}")
            raise

    async def request_vector_indexing(
        self, program_id: str, s3_paths: Dict[str, str]
    ) -> bool:
        """
        Vector DB 인덱싱을 위한 엔드포인트 호출

        Returns:
            bool: 인덱싱 요청 성공 여부
        """
        try:
            # TODO: Vector DB 인덱싱 엔드포인트 호출
            # 예시:
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "http://vector-db-service/index",
            #         json={
            #             "program_id": program_id,
            #             "s3_paths": s3_paths
            #         }
            #     )
            #     return response.status_code == 200

            logger.info(f"Vector DB 인덱싱 요청: program_id={program_id}")
            return True

        except Exception as e:
            logger.error(f"Vector DB 인덱싱 요청 실패: {str(e)}")
            return False
