"""Pydantic models for schema definitions."""

from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, field_validator, Field


class TableType(str, Enum):
    """Supported table types."""
    EXTERNAL = "EXTERNAL"
    MANAGED = "MANAGED"
    VIEW = "VIEW"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"


class VolumeType(str, Enum):
    """Supported volume types."""
    MANAGED = "MANAGED"
    EXTERNAL = "EXTERNAL"


class TableFormat(str, Enum):
    """Supported table formats."""
    DELTA = "DELTA"
    ICEBERG = "ICEBERG"
    PARQUET = "PARQUET"
    CSV = "CSV"
    JSON = "JSON"
    AVRO = "AVRO"
    ORC = "ORC"
    TEXT = "TEXT"


class ConstraintType(str, Enum):
    """Types of constraints."""
    PRIMARY_KEY = "PRIMARY_KEY"
    FOREIGN_KEY = "FOREIGN_KEY"
    CHECK = "CHECK"
    NOT_NULL = "NOT_NULL"


class ColumnType(str, Enum):
    """Supported column types."""
    STRING = "STRING"
    INT = "INT"
    BIGINT = "BIGINT"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMP_NTZ = "TIMESTAMP_NTZ"
    DATE = "DATE"
    BINARY = "BINARY"
    ARRAY = "ARRAY"
    MAP = "MAP"
    STRUCT = "STRUCT"


class Tag(BaseModel):
    """Tag definition for Unity Catalog objects."""
    key: str
    value: str
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v):
        if not v or not v.strip():
            raise ValueError("Tag key cannot be empty")
        return v.strip()


class Constraint(BaseModel):
    """Table constraint definition."""
    name: Optional[str] = None
    type: ConstraintType
    columns: List[str] = []
    expression: Optional[str] = None  # For CHECK constraints
    referenced_table: Optional[str] = None  # For FOREIGN KEY constraints
    referenced_columns: List[str] = []  # For FOREIGN KEY constraints
    
    # Constraint properties
    enforced: bool = True
    rely: bool = False  # RELY/NORELY for optimization
    deferrable: bool = False
    initially_deferred: bool = False
    
    @field_validator('columns')
    @classmethod
    def validate_columns(cls, v, info):
        constraint_type = info.data.get('type')
        if constraint_type in [ConstraintType.PRIMARY_KEY, ConstraintType.FOREIGN_KEY] and not v:
            raise ValueError(f"{constraint_type} constraint must specify columns")
        return v


class Column(BaseModel):
    """Table column definition."""
    name: str
    type: str  # More flexible than ColumnType enum to support complex types
    nullable: bool = True
    comment: Optional[str] = None
    default_value: Optional[str] = None
    position: Optional[int] = None
    
    # Column-level constraints
    primary_key: bool = False
    
    # Column masking and filtering
    mask_expression: Optional[str] = None
    
    # Tags for columns
    tags: List[Tag] = []
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v.strip()


class ClusteringSpec(BaseModel):
    """Liquid clustering specification."""
    columns: List[str]
    
    @field_validator('columns')
    @classmethod
    def validate_columns(cls, v):
        if not v:
            raise ValueError("Clustering columns cannot be empty")
        return v


class Table(BaseModel):
    """Table definition."""
    name: str
    type: TableType = TableType.MANAGED
    format: TableFormat = TableFormat.DELTA
    comment: Optional[str] = None
    location: Optional[str] = None  # For external tables
    columns: List[Column] = []
    properties: Dict[str, str] = {}
    partitioned_by: List[str] = []
    
    # Constraints
    constraints: List[Constraint] = []
    
    # Clustering
    cluster_by: Optional[ClusteringSpec] = None
    
    # Row-level security
    row_filter: Optional[str] = None
    
    # Ownership and metadata
    owner: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Tags
    tags: List[Tag] = []
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Table name cannot be empty")
        return v.strip()
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v, info):
        # External tables must have a location
        if info.data.get('type') == TableType.EXTERNAL and not v:
            raise ValueError("External tables must specify a location")
        return v
    
    def get_primary_key_constraint(self) -> Optional[Constraint]:
        """Get the primary key constraint if it exists."""
        return next((c for c in self.constraints if c.type == ConstraintType.PRIMARY_KEY), None)
    
    def get_foreign_key_constraints(self) -> List[Constraint]:
        """Get all foreign key constraints."""
        return [c for c in self.constraints if c.type == ConstraintType.FOREIGN_KEY]


class Volume(BaseModel):
    """Volume definition for non-tabular data."""
    name: str
    type: VolumeType = VolumeType.MANAGED
    comment: Optional[str] = None
    location: Optional[str] = None  # For external volumes
    
    # Ownership and metadata
    owner: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Tags
    tags: List[Tag] = []
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Volume name cannot be empty")
        return v.strip()
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v, info):
        # External volumes must have a location
        if info.data.get('type') == VolumeType.EXTERNAL and not v:
            raise ValueError("External volumes must specify a location")
        return v


class Schema(BaseModel):
    """Schema definition."""
    name: str
    comment: Optional[str] = None
    tables: List[Table] = []
    volumes: List[Volume] = []
    properties: Dict[str, str] = {}
    
    # Storage location for managed objects
    managed_location: Optional[str] = None
    
    # Ownership and metadata
    owner: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Tags
    tags: List[Tag] = []
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Schema name cannot be empty")
        return v.strip()


class Catalog(BaseModel):
    """Catalog definition."""
    name: str
    comment: Optional[str] = None
    properties: Dict[str, str] = {}
    
    # Storage location for managed objects
    managed_location: Optional[str] = None
    
    # Workspace binding
    bound_workspaces: List[str] = []
    
    # Ownership and metadata
    owner: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Tags
    tags: List[Tag] = []
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Catalog name cannot be empty")
        return v.strip()


class SchemaDefinition(BaseModel):
    """Complete schema definition."""
    catalog: Catalog
    schemas: List[Schema] = []
    
    def get_schema_by_name(self, name: str) -> Optional[Schema]:
        """Get schema by name."""
        return next((s for s in self.schemas if s.name == name), None)
    
    def get_table_by_name(self, schema_name: str, table_name: str) -> Optional[Table]:
        """Get table by schema and table name."""
        schema = self.get_schema_by_name(schema_name)
        if not schema:
            return None
        return next((t for t in schema.tables if t.name == table_name), None)
    
    def get_volume_by_name(self, schema_name: str, volume_name: str) -> Optional[Volume]:
        """Get volume by schema and volume name."""
        schema = self.get_schema_by_name(schema_name)
        if not schema:
            return None
        return next((v for v in schema.volumes if v.name == volume_name), None)


class CurrentState(BaseModel):
    """Current state of target environment."""
    catalog_exists: bool = False
    catalog_properties: Dict[str, str] = {}
    catalog_tags: List[Tag] = []
    schemas: Dict[str, Dict[str, Any]] = {}  # schema_name -> schema_info
    tables: Dict[str, Dict[str, Dict[str, Any]]] = {}  # schema_name -> table_name -> table_info
    volumes: Dict[str, Dict[str, Dict[str, Any]]] = {}  # schema_name -> volume_name -> volume_info
    
    def schema_exists(self, schema_name: str) -> bool:
        """Check if schema exists."""
        return schema_name in self.schemas
    
    def table_exists(self, schema_name: str, table_name: str) -> bool:
        """Check if table exists."""
        return (schema_name in self.tables and 
                table_name in self.tables[schema_name])
    
    def volume_exists(self, schema_name: str, volume_name: str) -> bool:
        """Check if volume exists."""
        return (schema_name in self.volumes and 
                volume_name in self.volumes[schema_name])
    
    def get_table_info(self, schema_name: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table information."""
        if not self.table_exists(schema_name, table_name):
            return None
        return self.tables[schema_name][table_name]
    
    def get_volume_info(self, schema_name: str, volume_name: str) -> Optional[Dict[str, Any]]:
        """Get volume information."""
        if not self.volume_exists(schema_name, volume_name):
            return None
        return self.volumes[schema_name][volume_name]


class ChangeScript(BaseModel):
    """Generated change script."""
    sql: str
    changes: List[str] = []
    warnings: List[str] = []
    
    def has_changes(self) -> bool:
        """Check if there are changes to apply."""
        return bool(self.changes)
    
    def summary(self) -> str:
        """Get summary of changes."""
        if not self.has_changes():
            return "No changes required"
        
        summary_lines = []
        for change in self.changes:
            summary_lines.append(f"• {change}")
        
        if self.warnings:
            summary_lines.append("\nWarnings:")
            for warning in self.warnings:
                summary_lines.append(f"⚠️  {warning}")
        
        return "\n".join(summary_lines) 