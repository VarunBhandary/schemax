"""YAML schema parser for Schemax."""

import yaml
from pathlib import Path
from typing import Dict, Any
from .models import SchemaDefinition, Catalog, Schema, Table, Column
from .exceptions import SchemaParsingError, ValidationError


class SchemaParser:
    """Parser for YAML schema definitions."""

    def parse_file(self, filepath: str) -> SchemaDefinition:
        """Parse schema definition from YAML file."""
        try:
            path = Path(filepath)
            if not path.exists():
                raise SchemaParsingError(f"Schema file not found: {filepath}")

            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return self.parse_dict(data)

        except yaml.YAMLError as e:
            raise SchemaParsingError(f"Invalid YAML in {filepath}: {e}")
        except Exception as e:
            raise SchemaParsingError(f"Failed to parse schema file {filepath}: {e}")

    def parse_dict(self, data: Dict[str, Any]) -> SchemaDefinition:
        """Parse schema definition from dictionary."""
        try:
            # Validate required top-level keys
            if "catalog" not in data:
                raise ValidationError("Schema definition must include 'catalog'")

            # Parse catalog
            catalog_data = data["catalog"]
            if isinstance(catalog_data, str):
                catalog = Catalog(name=catalog_data)
            else:
                catalog = Catalog(**catalog_data)

            # Parse schemas
            schemas = []
            if "schemas" in data:
                for schema_data in data["schemas"]:
                    schema = self._parse_schema(schema_data)
                    schemas.append(schema)

            return SchemaDefinition(catalog=catalog, schemas=schemas)

        except ValidationError:
            raise
        except Exception as e:
            raise SchemaParsingError(f"Failed to parse schema definition: {e}")

    def _parse_schema(self, schema_data: Dict[str, Any]) -> Schema:
        """Parse a single schema definition."""
        if "name" not in schema_data:
            raise ValidationError("Schema must have a 'name' field")

        # Parse tables
        tables = []
        if "tables" in schema_data:
            for table_data in schema_data["tables"]:
                table = self._parse_table(table_data)
                tables.append(table)

        # Create schema object
        schema_dict = {"name": schema_data["name"], "tables": tables}

        # Add optional fields
        for field in ["comment", "properties"]:
            if field in schema_data:
                schema_dict[field] = schema_data[field]

        return Schema(**schema_dict)

    def _parse_table(self, table_data: Dict[str, Any]) -> Table:
        """Parse a single table definition."""
        if "name" not in table_data:
            raise ValidationError("Table must have a 'name' field")

        # Parse columns
        columns = []
        if "columns" in table_data:
            for column_data in table_data["columns"]:
                column = self._parse_column(column_data)
                columns.append(column)

        # Create table object
        table_dict = {"name": table_data["name"], "columns": columns}

        # Add optional fields with defaults
        for field in ["type", "comment", "location", "properties", "partitioned_by"]:
            if field in table_data:
                table_dict[field] = table_data[field]

        return Table(**table_dict)

    def _parse_column(self, column_data: Dict[str, Any]) -> Column:
        """Parse a single column definition."""
        if isinstance(column_data, str):
            # Simple format: just column name
            return Column(name=column_data, type="STRING")

        if "name" not in column_data:
            raise ValidationError("Column must have a 'name' field")

        if "type" not in column_data:
            raise ValidationError(
                f"Column '{column_data['name']}' must have a 'type' field"
            )

        # Create column object
        column_dict = {"name": column_data["name"], "type": column_data["type"]}

        # Add optional fields
        for field in ["nullable", "comment", "default_value"]:
            if field in column_data:
                column_dict[field] = column_data[field]

        return Column(**column_dict)

    def validate_schema(self, schema_def: SchemaDefinition) -> None:
        """Validate schema definition for common issues."""
        errors = []

        # Check for duplicate schema names
        schema_names = [s.name for s in schema_def.schemas]
        if len(schema_names) != len(set(schema_names)):
            errors.append("Duplicate schema names found")

        # Check each schema
        for schema in schema_def.schemas:
            # Check for duplicate table names within schema
            table_names = [t.name for t in schema.tables]
            if len(table_names) != len(set(table_names)):
                errors.append(f"Duplicate table names in schema '{schema.name}'")

            # Check each table
            for table in schema.tables:
                # Check for duplicate column names within table
                column_names = [c.name for c in table.columns]
                if len(column_names) != len(set(column_names)):
                    errors.append(
                        f"Duplicate column names in table '{schema.name}.{table.name}'"
                    )

                # Validate external table has location
                if table.type == "EXTERNAL" and not table.location:
                    errors.append(
                        f"External table '{schema.name}.{table.name}' must specify a location"
                    )

        if errors:
            raise ValidationError(f"Schema validation failed: {'; '.join(errors)}")
