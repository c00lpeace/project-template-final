# _*_ coding: utf-8 _*_
"""
PLC 및 Program 관련 모델 정의
Program, ProcessingFailure, PLC, 기준정보 마스터 테이블들
ProgramLLMDataChunk, Template, TemplateData, KnowledgeReference (새로 추가됨)
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.sql.expression import false, true

from .models import Base


class Program(Base):
    """프로그램 마스터 테이블"""

    __tablename__ = "PROGRAMS"

    # 기본 정보
    program_id = Column("PROGRAM_ID", String(50), primary_key=True)
    program_name = Column("PROGRAM_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 상태 정보
    status = Column(
        "STATUS",
        String(50),
        nullable=False,
        default="preparing",
        server_default="preparing",
    )
    error_message = Column("ERROR_MESSAGE", Text, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)
    completed_at = Column("COMPLETED_AT", DateTime, nullable=True)

    # 사용 여부
    is_used = Column("IS_USED", Boolean, nullable=False, server_default=true())

    # 상태 상수
    STATUS_PREPARING = "preparing"
    STATUS_UPLOADING = "uploading"
    STATUS_PROCESSING = "processing"
    STATUS_EMBEDDING = "embedding"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __repr__(self):
        return f"<Program(program_id='{self.program_id}', name='{self.program_name}', status='{self.status}')>"


class ProcessingFailure(Base):
    """처리 실패 정보 및 재시도 관리 테이블"""

    __tablename__ = "PROCESSING_FAILURES"

    # 기본 정보
    failure_id = Column("FAILURE_ID", String(50), primary_key=True)
    program_id = Column(
        "PROGRAM_ID",
        String(50),
        ForeignKey("PROGRAMS.PROGRAM_ID"),
        nullable=False,
        index=True,
    )

    # 실패 정보
    failure_type = Column("FAILURE_TYPE", String(50), nullable=False, index=True)
    file_path = Column("FILE_PATH", String(500), nullable=True)
    file_index = Column("FILE_INDEX", Integer, nullable=True)
    filename = Column("FILENAME", String(255), nullable=True)
    s3_path = Column("S3_PATH", String(500), nullable=True)
    s3_key = Column("S3_KEY", String(500), nullable=True)

    # 에러 정보
    error_message = Column("ERROR_MESSAGE", Text, nullable=False)
    error_details = Column("ERROR_DETAILS", JSON, nullable=True)

    # 재시도 정보
    retry_count = Column("RETRY_COUNT", Integer, nullable=False, server_default="0")
    max_retry_count = Column(
        "MAX_RETRY_COUNT", Integer, nullable=False, server_default="3"
    )
    status = Column(
        "STATUS", String(50), nullable=False, default="pending", server_default="pending"
    )

    # 해결 정보
    resolved_at = Column("RESOLVED_AT", DateTime, nullable=True)
    last_retry_at = Column("LAST_RETRY_AT", DateTime, nullable=True)
    resolved_by = Column("RESOLVED_BY", String(50), nullable=True)

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    created_at = Column(
        "CREATED_AT", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # 실패 타입 상수
    FAILURE_TYPE_PREPROCESSING = "preprocessing"
    FAILURE_TYPE_DOCUMENT_STORAGE = "document_storage"
    FAILURE_TYPE_VECTOR_INDEXING = "vector_indexing"

    # 상태 상수
    STATUS_PENDING = "pending"
    STATUS_RETRYING = "retrying"
    STATUS_RESOLVED = "resolved"
    STATUS_FAILED = "failed"

    def __repr__(self):
        return f"<ProcessingFailure(failure_id='{self.failure_id}', program_id='{self.program_id}', failure_type='{self.failure_type}', status='{self.status}')>"


class PlantMaster(Base):
    """공장 기준정보 마스터 테이블"""

    __tablename__ = "PLANT_MASTER"

    # 기본 정보
    plant_id = Column("PLANT_ID", String(50), primary_key=True)
    plant_code = Column("PLANT_CODE", String(50), unique=True, nullable=False, index=True)
    plant_name = Column("PLANT_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    def __repr__(self):
        return f"<PlantMaster(plant_id='{self.plant_id}', plant_code='{self.plant_code}', plant_name='{self.plant_name}')>"


class ProcessMaster(Base):
    """공정 기준정보 마스터 테이블"""

    __tablename__ = "PROCESS_MASTER"

    # 기본 정보
    process_id = Column("PROCESS_ID", String(50), primary_key=True)
    process_code = Column("PROCESS_CODE", String(50), unique=True, nullable=False, index=True)
    process_name = Column("PROCESS_NAME", String(255), nullable=False)
    plant_id = Column(
        "PLANT_ID",
        String(50),
        ForeignKey("PLANT_MASTER.PLANT_ID"),
        nullable=False,
        index=True,
    )
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    def __repr__(self):
        return f"<ProcessMaster(process_id='{self.process_id}', process_code='{self.process_code}', process_name='{self.process_name}')>"


class LineMaster(Base):
    """라인 기준정보 마스터 테이블"""

    __tablename__ = "LINE_MASTER"

    # 기본 정보
    line_id = Column("LINE_ID", String(50), primary_key=True)
    line_code = Column("LINE_CODE", String(50), unique=True, nullable=False, index=True)
    line_name = Column("LINE_NAME", String(255), nullable=False)
    process_id = Column(
        "PROCESS_ID",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=False,
        index=True,
    )
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    def __repr__(self):
        return f"<LineMaster(line_id='{self.line_id}', line_code='{self.line_code}', line_name='{self.line_name}')>"


class EquipmentGroupMaster(Base):
    """장비 그룹 기준정보 마스터 테이블"""

    __tablename__ = "EQUIPMENT_GROUP_MASTER"

    # 기본 정보
    equipment_group_id = Column("EQUIPMENT_GROUP_ID", String(50), primary_key=True)
    equipment_group_code = Column(
        "EQUIPMENT_GROUP_CODE", String(50), unique=True, nullable=False, index=True
    )
    equipment_group_name = Column("EQUIPMENT_GROUP_NAME", String(255), nullable=False)
    line_id = Column(
        "LINE_ID",
        String(50),
        ForeignKey("LINE_MASTER.LINE_ID"),
        nullable=False,
        index=True,
    )
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    def __repr__(self):
        return f"<EquipmentGroupMaster(equipment_group_id='{self.equipment_group_id}', equipment_group_code='{self.equipment_group_code}', equipment_group_name='{self.equipment_group_name}')>"


class PLC(Base):
    """PLC 기준 정보 및 Program 매핑 테이블 (기준정보 스냅샷 포함)"""

    __tablename__ = "PLC"

    # 기본 정보
    id = Column("ID", String(50), primary_key=True)
    plc_id = Column("PLC_ID", String(50), nullable=False, index=True)  # PLC 식별자 (중복 가능)
    plc_name = Column("PLC_NAME", String(255), nullable=False)
    unit = Column("UNIT", String(100), nullable=True)

    # Program 매핑
    program_id = Column(
        "PROGRAM_ID",
        String(50),
        ForeignKey("PROGRAMS.PROGRAM_ID"),
        nullable=True,
        unique=True,
        index=True,
    )  # PLC 1개 → Program 1개 (unique)
    mapping_dt = Column("MAPPING_DT", DateTime, nullable=True)
    mapping_user = Column("MAPPING_USER", String(50), nullable=True)

    # 활성화 여부
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    # 기준정보 스냅샷 (PLC 생성/수정 시점의 기준정보 저장, 불변)
    plant_id_snapshot = Column("PLANT_ID_SNAPSHOT", String(50), nullable=True)
    plant_code_snapshot = Column("PLANT_CODE_SNAPSHOT", String(50), nullable=True)
    plant_name_snapshot = Column("PLANT_NAME_SNAPSHOT", String(255), nullable=True)

    process_id_snapshot = Column("PROCESS_ID_SNAPSHOT", String(50), nullable=True)
    process_code_snapshot = Column("PROCESS_CODE_SNAPSHOT", String(50), nullable=True)
    process_name_snapshot = Column("PROCESS_NAME_SNAPSHOT", String(255), nullable=True)

    line_id_snapshot = Column("LINE_ID_SNAPSHOT", String(50), nullable=True)
    line_code_snapshot = Column("LINE_CODE_SNAPSHOT", String(50), nullable=True)
    line_name_snapshot = Column("LINE_NAME_SNAPSHOT", String(255), nullable=True)

    equipment_group_id_snapshot = Column(
        "EQUIPMENT_GROUP_ID_SNAPSHOT", String(50), nullable=True
    )
    equipment_group_code_snapshot = Column(
        "EQUIPMENT_GROUP_CODE_SNAPSHOT", String(50), nullable=True
    )
    equipment_group_name_snapshot = Column(
        "EQUIPMENT_GROUP_NAME_SNAPSHOT", String(255), nullable=True
    )

    # 현재 기준정보 참조 (nullable, 선택 시 사용)
    plant_id_current = Column(
        "PLANT_ID_CURRENT",
        String(50),
        ForeignKey("PLANT_MASTER.PLANT_ID"),
        nullable=True,
        index=True,
    )
    process_id_current = Column(
        "PROCESS_ID_CURRENT",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=True,
        index=True,
    )
    line_id_current = Column(
        "LINE_ID_CURRENT",
        String(50),
        ForeignKey("LINE_MASTER.LINE_ID"),
        nullable=True,
        index=True,
    )
    equipment_group_id_current = Column(
        "EQUIPMENT_GROUP_ID_CURRENT",
        String(50),
        ForeignKey("EQUIPMENT_GROUP_MASTER.EQUIPMENT_GROUP_ID"),
        nullable=True,
        index=True,
    )

    def __repr__(self):
        return f"<PLC(id='{self.id}', plc_id='{self.plc_id}', plc_name='{self.plc_name}', program_id='{self.program_id}')>"


class ProgramLLMDataChunk(Base):
    """프로그램 LLM 데이터 청크 테이블"""
    __tablename__ = "PROGRAM_LLM_DATA_CHUNKS"
    
    # 기본 정보
    chunk_id = Column('CHUNK_ID', String(50), primary_key=True)
    program_id = Column('PROGRAM_ID', String(50), ForeignKey('PROGRAMS.PROGRAM_ID'), nullable=False, index=True)
    data_type = Column('DATA_TYPE', String(50), nullable=False, index=True)
    data_version = Column('DATA_VERSION', String(50), nullable=True, index=True)
    
    # 청크 정보
    chunk_index = Column('CHUNK_INDEX', Integer, nullable=False)
    total_chunks = Column('TOTAL_CHUNKS', Integer, nullable=False)
    chunk_size = Column('CHUNK_SIZE', Integer, nullable=False)
    total_size = Column('TOTAL_SIZE', Integer, nullable=True)
    
    # S3 정보
    s3_bucket = Column('S3_BUCKET', String(255), nullable=True)
    s3_key = Column('S3_KEY', String(500), nullable=False)
    s3_url = Column('S3_URL', String(1000), nullable=True)
    
    # 체크섬 정보
    file_hash = Column('FILE_HASH', String(64), nullable=True)
    checksum = Column('CHECKSUM', String(64), nullable=True)
    
    # 설명 및 메타데이터
    description = Column('DESCRIPTION', Text, nullable=True)
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    
    # 시간 정보
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ProgramLLMDataChunk(chunk_id='{self.chunk_id}', program_id='{self.program_id}', data_type='{self.data_type}')>"


class Template(Base):
    """템플릿 테이블"""
    __tablename__ = "TEMPLATES"
    
    # 기본 정보
    template_id = Column('TEMPLATE_ID', String(50), primary_key=True)
    document_id = Column('DOCUMENT_ID', String(50), ForeignKey('DOCUMENTS.DOCUMENT_ID'), nullable=False, index=True)
    program_id = Column('PROGRAM_ID', String(50), ForeignKey('PROGRAMS.PROGRAM_ID'), nullable=True, index=True)
    
    # 메타데이터
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    
    # 시간 정보
    created_at = Column('CREATED_AT', DateTime, nullable=False, server_default=func.now())
    created_by = Column('CREATED_BY', String(50), nullable=False)

    def __repr__(self):
        return f"<Template(template_id='{self.template_id}', document_id='{self.document_id}')>"


class TemplateData(Base):
    """템플릿 데이터 테이블"""
    __tablename__ = "TEMPLATE_DATA"
    
    # 기본 정보
    template_data_id = Column('TEMPLATE_DATA_ID', String(50), primary_key=True)
    template_id = Column('TEMPLATE_ID', String(50), ForeignKey('TEMPLATES.TEMPLATE_ID'), nullable=False, index=True)
    
    # 폴더 정보
    folder_id = Column('FOLDER_ID', String(100), nullable=True, index=True)
    folder_name = Column('FOLDER_NAME', String(200), nullable=True)
    sub_folder_name = Column('SUB_FOLDER_NAME', String(200), nullable=True)
    
    # 로직 정보
    logic_id = Column('LOGIC_ID', String(100), nullable=False, index=True)
    logic_name = Column('LOGIC_NAME', String(200), nullable=False)
    
    # 문서 참조
    document_id = Column('DOCUMENT_ID', String(50), ForeignKey('DOCUMENTS.DOCUMENT_ID'), nullable=True, index=True)
    row_index = Column('ROW_INDEX', Integer, nullable=False)
    
    # 메타데이터
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    
    # 시간 정보
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column('CREATED_AT', DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<TemplateData(template_data_id='{self.template_data_id}', template_id='{self.template_id}', logic_id='{self.logic_id}')>"


class KnowledgeReference(Base):
    """Knowledge Base 참조 정보 테이블 (매뉴얼, 용어집, PLC 레포)"""
    __tablename__ = "KNOWLEDGE_REFERENCES"
    
    # 기본 정보
    reference_id = Column('REFERENCE_ID', String(50), primary_key=True)
    reference_type = Column('REFERENCE_TYPE', String(50), nullable=False, index=True)  # manual, glossary, plc
    name = Column('NAME', String(255), nullable=False)
    version = Column('VERSION', String(50), nullable=True)
    is_latest = Column('IS_LATEST', Boolean, nullable=False, server_default=false())
    
    # 레포 및 데이터소스 정보
    repo_id = Column('REPO_ID', String(255), nullable=False, index=True)
    datasource_id = Column('DATASOURCE_ID', String(255), nullable=False, index=True)
    file_id = Column('FILE_ID', String(255), nullable=True)
    
    # 설명 및 메타데이터
    description = Column('DESCRIPTION', Text, nullable=True)
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    
    # 활성화 여부
    is_active = Column('IS_ACTIVE', Boolean, nullable=False, server_default=true())
    
    # 시간 정보
    created_at = Column('CREATED_AT', DateTime, nullable=False, server_default=func.now())
    created_by = Column('CREATED_BY', String(50), nullable=False)
    updated_at = Column('UPDATED_AT', DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column('UPDATED_BY', String(50), nullable=True)

    def __repr__(self):
        return f"<KnowledgeReference(reference_id='{self.reference_id}', name='{self.name}', type='{self.reference_type}')>"
