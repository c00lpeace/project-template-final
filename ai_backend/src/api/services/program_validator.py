# _*_ coding: utf-8 _*_
"""Program validation module for file validation."""
import io
import logging
import zipfile
from typing import Dict, List, Tuple

import pandas as pd
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class ProgramValidator:
    """프로그램 파일 유효성 검사 클래스"""

    REQUIRED_XLSX_COLUMNS = [
        "로직파일명",
        "분류",
        "템플릿명",
    ]  # 예시 컬럼명, 실제 컬럼명에 맞게 수정 필요
    REQUIRED_CSV_COLUMNS = [
        "파일명",
        "디바이스명",
        "설명",
    ]  # 예시 컬럼명, 실제 컬럼명에 맞게 수정 필요

    @staticmethod
    def validate_files(
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
    ) -> Tuple[bool, List[str], List[str], List[str]]:
        """
        파일 유효성 검사

        Returns:
            Tuple[bool, List[str], List[str], List[str]]:
                (is_valid, errors, warnings, checked_files)
        """
        errors = []
        warnings = []
        checked_files = []

        try:
            # 1. ZIP 파일 검증
            zip_errors, zip_warnings, zip_files = ProgramValidator._validate_zip_file(
                ladder_zip
            )
            errors.extend(zip_errors)
            warnings.extend(zip_warnings)
            checked_files.extend(zip_files)

            # 2. XLSX 파일 검증 및 컬럼 확인
            xlsx_errors, xlsx_warnings, xlsx_files = (
                ProgramValidator._validate_xlsx_file(classification_xlsx)
            )
            errors.extend(xlsx_errors)
            warnings.extend(xlsx_warnings)
            checked_files.extend(xlsx_files)

            # 3. CSV 파일 검증 및 컬럼 확인
            csv_errors, csv_warnings, csv_files = ProgramValidator._validate_csv_file(
                device_comment_csv
            )
            errors.extend(csv_errors)
            warnings.extend(csv_warnings)
            checked_files.extend(csv_files)

            # 4. XLSX의 로직파일명이 ZIP에 있는지 확인
            if not errors:  # 에러가 없을 때만 교차 검증
                cross_errors = ProgramValidator._validate_file_cross_reference(
                    ladder_zip, classification_xlsx
                )
                errors.extend(cross_errors)

            is_valid = len(errors) == 0

            return is_valid, errors, warnings, checked_files

        except Exception as e:
            logger.error(f"유효성 검사 중 예외 발생: {str(e)}")
            errors.append(f"유효성 검사 중 오류 발생: {str(e)}")
            return False, errors, warnings, checked_files

    @staticmethod
    def _validate_zip_file(
        zip_file: UploadFile,
    ) -> Tuple[List[str], List[str], List[str]]:
        """ZIP 파일 유효성 검사"""
        errors = []
        warnings = []
        checked_files = []

        try:
            # 파일 읽기
            zip_file.file.seek(0)
            zip_content = zip_file.file.read()
            zip_file.file.seek(0)

            # ZIP 파일 형식 확인
            if not zipfile.is_zipfile(io.BytesIO(zip_content)):
                errors.append(f"{zip_file.filename}은(는) 유효한 ZIP 파일이 아닙니다.")
                return errors, warnings, checked_files

            # ZIP 파일 내용 확인
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                file_list = zip_ref.namelist()
                checked_files = file_list

                if len(file_list) == 0:
                    errors.append(f"{zip_file.filename}은(는) 비어있는 ZIP 파일입니다.")
                else:
                    logger.info(f"ZIP 파일 검증 완료: {len(file_list)}개 파일 발견")

        except Exception as e:
            errors.append(f"ZIP 파일 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files

    @staticmethod
    def _validate_xlsx_file(
        xlsx_file: UploadFile,
    ) -> Tuple[List[str], List[str], List[str]]:
        """XLSX 파일 유효성 검사 및 컬럼 확인"""
        errors = []
        warnings = []
        checked_files = []

        try:
            # 파일 읽기
            xlsx_file.file.seek(0)
            xlsx_content = xlsx_file.file.read()
            xlsx_file.file.seek(0)

            # XLSX 파일 읽기
            df = pd.read_excel(io.BytesIO(xlsx_content))

            # 필수 컬럼 확인
            missing_columns = []
            for col in ProgramValidator.REQUIRED_XLSX_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)

            if missing_columns:
                errors.append(
                    f"XLSX 파일에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. "
                    f"현재 컬럼: {', '.join(df.columns.tolist())}"
                )
            else:
                # 로직파일명 리스트 추출
                if "로직파일명" in df.columns:
                    logic_files = df["로직파일명"].dropna().tolist()
                    checked_files = logic_files
                    logger.info(
                        f"XLSX 파일 검증 완료: {len(logic_files)}개 로직 파일명 발견"
                    )
                else:
                    errors.append("XLSX 파일에 '로직파일명' 컬럼을 찾을 수 없습니다.")

        except Exception as e:
            errors.append(f"XLSX 파일 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files

    @staticmethod
    def _validate_csv_file(
        csv_file: UploadFile,
    ) -> Tuple[List[str], List[str], List[str]]:
        """CSV 파일 유효성 검사 및 컬럼 확인"""
        errors = []
        warnings = []
        checked_files = []

        try:
            # 파일 읽기
            csv_file.file.seek(0)
            csv_content = csv_file.file.read()
            csv_file.file.seek(0)

            # CSV 파일 읽기 (인코딩 자동 감지 시도)
            try:
                df = pd.read_csv(io.BytesIO(csv_content), encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(csv_content), encoding="cp949")
                except:
                    df = pd.read_csv(io.BytesIO(csv_content), encoding="latin-1")

            # 필수 컬럼 확인
            missing_columns = []
            for col in ProgramValidator.REQUIRED_CSV_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)

            if missing_columns:
                errors.append(
                    f"CSV 파일에 필수 컬럼이 없습니다: {', '.join(missing_columns)}. "
                    f"현재 컬럼: {', '.join(df.columns.tolist())}"
                )
            else:
                # 파일명 리스트 추출
                if "파일명" in df.columns:
                    device_files = df["파일명"].dropna().tolist()
                    checked_files = device_files
                    logger.info(
                        f"CSV 파일 검증 완료: {len(device_files)}개 디바이스 파일명 발견"
                    )

        except Exception as e:
            errors.append(f"CSV 파일 검증 중 오류: {str(e)}")

        return errors, warnings, checked_files

    @staticmethod
    def _validate_file_cross_reference(
        ladder_zip: UploadFile, classification_xlsx: UploadFile
    ) -> List[str]:
        """XLSX의 로직파일명이 ZIP 파일에 실제로 있는지 교차 검증"""
        errors = []

        try:
            # ZIP 파일 내용 읽기
            ladder_zip.file.seek(0)
            zip_content = ladder_zip.file.read()
            ladder_zip.file.seek(0)

            # XLSX 파일 내용 읽기
            classification_xlsx.file.seek(0)
            xlsx_content = classification_xlsx.file.read()
            classification_xlsx.file.seek(0)

            # ZIP 파일 내 파일 목록 추출
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                zip_files = set(zip_ref.namelist())

            # XLSX 파일에서 로직파일명 추출
            df = pd.read_excel(io.BytesIO(xlsx_content))
            if "로직파일명" not in df.columns:
                errors.append("XLSX 파일에 '로직파일명' 컬럼을 찾을 수 없습니다.")
                return errors

            logic_files = df["로직파일명"].dropna().tolist()

            # ZIP 파일에 없는 파일명 확인
            missing_files = []
            for logic_file in logic_files:
                # 파일명 정규화 (경로 구분자 통일)
                normalized_logic_file = logic_file.replace("\\", "/")
                found = False

                # 정확히 일치하거나, 파일명만 일치하는지 확인
                for zip_file in zip_files:
                    normalized_zip_file = zip_file.replace("\\", "/")
                    if (
                        normalized_logic_file == normalized_zip_file
                        or normalized_logic_file == normalized_zip_file.split("/")[-1]
                    ):
                        found = True
                        break

                if not found:
                    missing_files.append(logic_file)

            if missing_files:
                errors.append(
                    f"분류체계 데이터에 있는 {len(missing_files)}개 파일이 ZIP 파일에 없습니다: "
                    f"{', '.join(missing_files[:10])}"  # 처음 10개만 표시
                )

            logger.info(
                f"교차 검증 완료: {len(logic_files)}개 파일 중 {len(logic_files) - len(missing_files)}개 확인됨"
            )

        except Exception as e:
            errors.append(f"교차 검증 중 오류: {str(e)}")

        return errors
