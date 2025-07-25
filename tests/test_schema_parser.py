"""Tests for schema parser."""

import pytest

from schemax.exceptions import SchemaParsingError, ValidationError
from schemax.models import Catalog, Column, Schema, SchemaDefinition, Table
from schemax.schema_parser import SchemaParser


def test_parse_simple_schema():
    """Test parsing a simple schema definition."""
    parser = SchemaParser()

    schema_data = {
        "catalog": "test_catalog",
        "schemas": [
            {
                "name": "test_schema",
                "tables": [
                    {
                        "name": "test_table",
                        "columns": [
                            {"name": "id", "type": "BIGINT", "nullable": False}
                        ],
                    }
                ],
            }
        ],
    }

    result = parser.parse_dict(schema_data)

    assert isinstance(result, SchemaDefinition)
    assert result.catalog.name == "test_catalog"
    assert len(result.schemas) == 1
    assert result.schemas[0].name == "test_schema"
    assert len(result.schemas[0].tables) == 1
    assert result.schemas[0].tables[0].name == "test_table"


def test_parse_external_table():
    """Test parsing external table with location."""
    parser = SchemaParser()

    schema_data = {
        "catalog": "test_catalog",
        "schemas": [
            {
                "name": "test_schema",
                "tables": [
                    {
                        "name": "external_table",
                        "type": "EXTERNAL",
                        "location": "s3://bucket/path/",
                        "columns": [{"name": "data", "type": "STRING"}],
                    }
                ],
            }
        ],
    }

    result = parser.parse_dict(schema_data)
    table = result.schemas[0].tables[0]

    assert table.type.value == "EXTERNAL"
    assert table.location == "s3://bucket/path/"


def test_validation_duplicate_schemas():
    """Test validation catches duplicate schema names."""
    parser = SchemaParser()

    schema_data = {
        "catalog": "test_catalog",
        "schemas": [
            {"name": "duplicate_name", "tables": []},
            {"name": "duplicate_name", "tables": []},
        ],
    }

    schema_def = parser.parse_dict(schema_data)

    with pytest.raises(ValidationError, match="Duplicate schema names"):
        parser.validate_schema(schema_def)


def test_validation_missing_location_external_table():
    """Test validation catches external tables without location."""
    parser = SchemaParser()

    schema_data = {
        "catalog": "test_catalog",
        "schemas": [
            {
                "name": "test_schema",
                "tables": [
                    {
                        "name": "external_table",
                        "type": "EXTERNAL",
                        # Missing location
                        "columns": [{"name": "data", "type": "STRING"}],
                    }
                ],
            }
        ],
    }

    schema_def = parser.parse_dict(schema_data)

    with pytest.raises(ValidationError, match="must specify a location"):
        parser.validate_schema(schema_def)


def test_missing_catalog():
    """Test error when catalog is missing."""
    parser = SchemaParser()

    schema_data = {"schemas": [{"name": "test_schema", "tables": []}]}

    with pytest.raises(ValidationError, match="must include 'catalog'"):
        parser.parse_dict(schema_data)
