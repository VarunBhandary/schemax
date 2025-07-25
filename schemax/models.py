"""Pydantic models for schema definitions."""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, field_validator


class TableType(str, Enum):
    """Supported table types."""
    EXTERNAL = "EXTERNAL"
    MANAGED = "MANAGED"
    VIEW = "VIEW"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"


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
    DATE = "DATE"
    BINARY = "BINARY"
    ARRAY = "ARRAY"
    MAP = "MAP"
    STRUCT = "STRUCT"


class Column(BaseModel):
    """Table column definition."""
    name: str
    type: str  # More flexible than ColumnType enum to support complex types
    nullable: bool = True
    comment: Optional[str] = None
    default_value: Optional[str] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v.strip()


class Table(BaseModel):
    """Table definition."""
    name: str
    type: TableType = TableType.MANAGED
    comment: Optional[str] = None
    location: Optional[str] = None  # For external tables
    columns: List[Column] = []
    properties: Dict[str, str] = {}
    partitioned_by: List[str] = []
    
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


class Schema(BaseModel):
    """Schema definition."""
    name: str
    comment: Optional[str] = None
    tables: List[Table] = []
    properties: Dict[str, str] = {}
    
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


class CurrentState(BaseModel):
    """Current state of target environment."""
    catalog_exists: bool = False
    catalog_properties: Dict[str, str] = {}
    schemas: Dict[str, Dict[str, Any]] = {}  # schema_name -> schema_info
    tables: Dict[str, Dict[str, Dict[str, Any]]] = {}  # schema_name -> table_name -> table_info
    
    def schema_exists(self, schema_name: str) -> bool:
        """Check if schema exists."""
        return schema_name in self.schemas
    
    def table_exists(self, schema_name: str, table_name: str) -> bool:
        """Check if table exists."""
        return (schema_name in self.tables and 
                table_name in self.tables[schema_name])
    
    def get_table_info(self, schema_name: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Get table information."""
        if not self.table_exists(schema_name, table_name):
            return None
        return self.tables[schema_name][table_name]


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