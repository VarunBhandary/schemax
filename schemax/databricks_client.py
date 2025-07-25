"""Databricks client for environment inspection."""

from typing import Dict, List, Optional, Any
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound, PermissionDenied
from databricks.sdk.service.catalog import CatalogInfo, SchemaInfo, TableInfo, ColumnInfo

from .config import Config
from .models import CurrentState
from .exceptions import DatabricksConnectionError


class DatabricksClient:
    """Client for interacting with Databricks Unity Catalog."""
    
    def __init__(self, config: Config):
        """Initialize Databricks client."""
        self.config = config
        try:
            self.client = WorkspaceClient(
                host=config.databricks_host,
                token=config.databricks_token
            )
            # Test connection
            self.client.current_user.me()
        except Exception as e:
            raise DatabricksConnectionError(f"Failed to connect to Databricks: {e}")
    
    def get_current_state(self, catalog_name: str, schema_name: Optional[str] = None) -> CurrentState:
        """Get current state of target environment."""
        current_state = CurrentState()
        
        try:
            # Check if catalog exists
            try:
                catalog_info = self.client.catalogs.get(catalog_name)
                current_state.catalog_exists = True
                current_state.catalog_properties = catalog_info.properties or {}
            except NotFound:
                current_state.catalog_exists = False
                return current_state  # No point checking further if catalog doesn't exist
            
            # Get schemas
            if schema_name:
                # Check specific schema
                schema_info = self._get_schema_info(catalog_name, schema_name)
                if schema_info:
                    current_state.schemas[schema_name] = schema_info
                    # Get tables in this schema
                    tables = self._get_tables_in_schema(catalog_name, schema_name)
                    current_state.tables[schema_name] = tables
            else:
                # Get all schemas
                schemas = self.client.schemas.list(catalog_name=catalog_name)
                for schema in schemas:
                    schema_info = self._schema_to_dict(schema)
                    current_state.schemas[schema.name] = schema_info
                    # Get tables in this schema
                    tables = self._get_tables_in_schema(catalog_name, schema.name)
                    current_state.tables[schema.name] = tables
            
            return current_state
            
        except PermissionDenied as e:
            raise DatabricksConnectionError(f"Permission denied accessing catalog '{catalog_name}': {e}")
        except Exception as e:
            raise DatabricksConnectionError(f"Failed to inspect target environment: {e}")
    
    def _get_schema_info(self, catalog_name: str, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific schema."""
        try:
            schema = self.client.schemas.get(full_name=f"{catalog_name}.{schema_name}")
            return self._schema_to_dict(schema)
        except NotFound:
            return None
    
    def _get_tables_in_schema(self, catalog_name: str, schema_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all tables in a schema."""
        tables = {}
        try:
            table_list = self.client.tables.list(
                catalog_name=catalog_name,
                schema_name=schema_name
            )
            
            for table in table_list:
                table_info = self._table_to_dict(table)
                # Get detailed table info including columns
                try:
                    detailed_table = self.client.tables.get(full_name=table.full_name)
                    table_info.update(self._table_to_dict(detailed_table))
                except Exception:
                    # If we can't get detailed info, continue with basic info
                    pass
                
                tables[table.name] = table_info
                
        except NotFound:
            # Schema doesn't exist or no tables
            pass
        except Exception as e:
            raise DatabricksConnectionError(f"Failed to list tables in {catalog_name}.{schema_name}: {e}")
        
        return tables
    
    def _schema_to_dict(self, schema: SchemaInfo) -> Dict[str, Any]:
        """Convert SchemaInfo to dictionary."""
        return {
            'name': schema.name,
            'catalog_name': schema.catalog_name,
            'comment': schema.comment,
            'properties': schema.properties or {},
            'full_name': schema.full_name,
            'owner': schema.owner,
            'created_at': schema.created_at,
            'updated_at': schema.updated_at,
        }
    
    def _table_to_dict(self, table: TableInfo) -> Dict[str, Any]:
        """Convert TableInfo to dictionary."""
        table_dict = {
            'name': table.name,
            'catalog_name': table.catalog_name,
            'schema_name': table.schema_name,
            'table_type': table.table_type.value if table.table_type else None,
            'data_source_format': table.data_source_format,
            'comment': table.comment,
            'properties': table.properties or {},
            'owner': table.owner,
            'created_at': table.created_at,
            'updated_at': table.updated_at,
        }
        
        # Add storage info for external tables
        if table.storage_location:
            table_dict['storage_location'] = table.storage_location
        
        # Add columns if available
        if table.columns:
            table_dict['columns'] = [self._column_to_dict(col) for col in table.columns]
        
        return table_dict
    
    def _column_to_dict(self, column: ColumnInfo) -> Dict[str, Any]:
        """Convert ColumnInfo to dictionary."""
        return {
            'name': column.name,
            'type_text': column.type_text,
            'type_name': column.type_name.value if column.type_name else None,
            'nullable': column.nullable,
            'comment': column.comment,
            'position': column.position,
        }
    
    def execute_sql(self, sql: str, warehouse_id: Optional[str] = None) -> None:
        """Execute SQL statement."""
        if not warehouse_id:
            warehouse_id = self.config.databricks_warehouse_id
        
        if not warehouse_id:
            raise DatabricksConnectionError("Warehouse ID is required to execute SQL")
        
        try:
            # Execute SQL using SQL execution API
            response = self.client.statement_execution.execute_statement(
                statement=sql,
                warehouse_id=warehouse_id,
                wait_timeout='30s'
            )
            
            if response.status.state == 'FAILED':
                raise DatabricksConnectionError(f"SQL execution failed: {response.status.error}")
            
        except Exception as e:
            raise DatabricksConnectionError(f"Failed to execute SQL: {e}")
    
    def test_connection(self) -> bool:
        """Test Databricks connection."""
        try:
            self.client.current_user.me()
            return True
        except Exception:
            return False 