"""DSPy-powered change script generator."""

import dspy
from typing import List, Dict, Any, Optional
from .config import Config
from .models import SchemaDefinition, CurrentState, ChangeScript, Schema, Table, Column
from .databricks_client import DatabricksClient
from .exceptions import ChangeGenerationError


class DatabricksLLM(dspy.LM):
    """DSPy LLM adapter for Databricks LLM endpoints."""

    def __init__(self, config: Config, databricks_client: DatabricksClient):
        self.config = config
        self.client = databricks_client
        self.endpoint = config.llm_endpoint
        super().__init__(model=config.llm_endpoint)

    def basic_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Make a basic request to Databricks LLM endpoint."""
        try:
            # Use Databricks SDK to call serving endpoint
            response = self.client.client.serving_endpoints.query(
                name=self.endpoint,
                inputs=[
                    {
                        "prompt": prompt,
                        "max_tokens": kwargs.get(
                            "max_tokens", self.config.llm_max_tokens
                        ),
                        "temperature": kwargs.get(
                            "temperature", self.config.llm_temperature
                        ),
                    }
                ],
            )

            # Extract response text
            if response.predictions and len(response.predictions) > 0:
                prediction = response.predictions[0]
                if isinstance(prediction, dict) and "candidates" in prediction:
                    return {"choices": [{"text": prediction["candidates"][0]["text"]}]}
                elif isinstance(prediction, str):
                    return {"choices": [{"text": prediction}]}

            raise ChangeGenerationError("No valid response from LLM endpoint")

        except Exception as e:
            raise ChangeGenerationError(f"Failed to call LLM endpoint: {e}")


class SchemaAnalyzer(dspy.Signature):
    """Analyze differences between desired and current schema state."""

    desired_schema = dspy.InputField(
        desc="YAML schema definition describing desired state"
    )
    current_state = dspy.InputField(
        desc="JSON description of current Databricks environment state"
    )
    catalog_name = dspy.InputField(desc="Target catalog name")
    schema_name = dspy.InputField(desc="Target schema name (optional)")

    analysis = dspy.OutputField(
        desc="Detailed analysis of differences between desired and current state"
    )
    changes_needed = dspy.OutputField(
        desc="List of specific changes required to reach desired state"
    )


class SQLGenerator(dspy.Signature):
    """Generate SQL DDL statements to implement schema changes."""

    analysis = dspy.InputField(desc="Analysis of required changes")
    changes_needed = dspy.InputField(desc="List of specific changes to implement")
    catalog_name = dspy.InputField(desc="Target catalog name")
    schema_name = dspy.InputField(desc="Target schema name")

    sql_script = dspy.OutputField(
        desc="Complete SQL DDL script to implement all changes"
    )
    warnings = dspy.OutputField(
        desc="Any warnings or considerations for applying the changes"
    )


class ChangeValidator(dspy.Signature):
    """Validate generated SQL changes for correctness and safety."""

    sql_script = dspy.InputField(desc="Generated SQL DDL script")
    original_analysis = dspy.InputField(desc="Original change analysis")

    is_valid = dspy.OutputField(desc="Whether the SQL script is valid and safe")
    validation_issues = dspy.OutputField(
        desc="Any validation issues or improvements needed"
    )
    corrected_sql = dspy.OutputField(desc="Corrected SQL if issues were found")


# DSPy modules (chains)
class SchemaChangeAnalyzer(dspy.Module):
    """Analyze schema differences and determine required changes."""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(SchemaAnalyzer)

    def forward(
        self,
        desired_schema: str,
        current_state: str,
        catalog_name: str,
        schema_name: str = "",
    ):
        return self.analyze(
            desired_schema=desired_schema,
            current_state=current_state,
            catalog_name=catalog_name,
            schema_name=schema_name,
        )


class SQLScriptGenerator(dspy.Module):
    """Generate SQL script from change analysis."""

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(SQLGenerator)

    def forward(
        self, analysis: str, changes_needed: str, catalog_name: str, schema_name: str
    ):
        return self.generate(
            analysis=analysis,
            changes_needed=changes_needed,
            catalog_name=catalog_name,
            schema_name=schema_name,
        )


class SQLValidator(dspy.Module):
    """Validate generated SQL script."""

    def __init__(self):
        super().__init__()
        self.validate = dspy.ChainOfThought(ChangeValidator)

    def forward(self, sql_script: str, original_analysis: str):
        return self.validate(sql_script=sql_script, original_analysis=original_analysis)


class ChangeGenerator:
    """Generate change scripts using DSPy and Databricks LLM."""

    def __init__(self, config: Config, databricks_client: DatabricksClient):
        self.config = config
        self.client = databricks_client

        # Initialize DSPy with Databricks LLM
        self.llm = DatabricksLLM(config, databricks_client)
        dspy.configure(lm=self.llm, max_retries=config.dspy_max_retries)

        # Initialize DSPy modules
        self.analyzer = SchemaChangeAnalyzer()
        self.sql_generator = SQLScriptGenerator()
        self.validator = SQLValidator()

    def generate_changes(
        self, schema_def: SchemaDefinition, current_state: CurrentState
    ) -> ChangeScript:
        """Generate change script by comparing desired vs current state."""
        try:
            # Convert inputs to string representations for LLM
            desired_schema_str = self._schema_def_to_string(schema_def)
            current_state_str = self._current_state_to_string(current_state)

            # Step 1: Analyze differences
            analysis_result = self.analyzer(
                desired_schema=desired_schema_str,
                current_state=current_state_str,
                catalog_name=schema_def.catalog.name,
                schema_name="",  # Analyze all schemas
            )

            # Step 2: Generate SQL script
            sql_result = self.sql_generator(
                analysis=analysis_result.analysis,
                changes_needed=analysis_result.changes_needed,
                catalog_name=schema_def.catalog.name,
                schema_name="",
            )

            # Step 3: Validate SQL script
            validation_result = self.validator(
                sql_script=sql_result.sql_script,
                original_analysis=analysis_result.analysis,
            )

            # Use corrected SQL if validation found issues
            final_sql = sql_result.sql_script
            warnings = []

            if (
                hasattr(validation_result, "is_valid")
                and validation_result.is_valid.lower() == "false"
            ):
                if (
                    hasattr(validation_result, "corrected_sql")
                    and validation_result.corrected_sql
                ):
                    final_sql = validation_result.corrected_sql
                if hasattr(validation_result, "validation_issues"):
                    warnings.append(
                        f"SQL validation issues: {validation_result.validation_issues}"
                    )

            # Parse warnings from SQL generator
            if hasattr(sql_result, "warnings") and sql_result.warnings:
                warnings.append(sql_result.warnings)

            # Extract list of changes from analysis
            changes = self._extract_changes_list(analysis_result.changes_needed)

            return ChangeScript(sql=final_sql, changes=changes, warnings=warnings)

        except Exception as e:
            raise ChangeGenerationError(f"Failed to generate change script: {e}")

    def _schema_def_to_string(self, schema_def: SchemaDefinition) -> str:
        """Convert schema definition to string representation."""
        result = []
        result.append(f"Catalog: {schema_def.catalog.name}")
        if schema_def.catalog.comment:
            result.append(f"  Comment: {schema_def.catalog.comment}")

        for schema in schema_def.schemas:
            result.append(f"\nSchema: {schema.name}")
            if schema.comment:
                result.append(f"  Comment: {schema.comment}")

            for table in schema.tables:
                result.append(f"  Table: {table.name} (Type: {table.type})")
                if table.comment:
                    result.append(f"    Comment: {table.comment}")
                if table.location:
                    result.append(f"    Location: {table.location}")

                for column in table.columns:
                    nullable_str = "NULL" if column.nullable else "NOT NULL"
                    result.append(
                        f"    Column: {column.name} {column.type} {nullable_str}"
                    )
                    if column.comment:
                        result.append(f"      Comment: {column.comment}")

        return "\n".join(result)

    def _current_state_to_string(self, current_state: CurrentState) -> str:
        """Convert current state to string representation."""
        result = []

        if current_state.catalog_exists:
            result.append("Catalog exists")
        else:
            result.append("Catalog does not exist")

        for schema_name, schema_info in current_state.schemas.items():
            result.append(f"\nSchema: {schema_name}")
            if schema_info.get("comment"):
                result.append(f"  Comment: {schema_info['comment']}")

            # Add tables in this schema
            schema_tables = current_state.tables.get(schema_name, {})
            for table_name, table_info in schema_tables.items():
                table_type = table_info.get("table_type", "UNKNOWN")
                result.append(f"  Table: {table_name} (Type: {table_type})")

                if table_info.get("comment"):
                    result.append(f"    Comment: {table_info['comment']}")
                if table_info.get("storage_location"):
                    result.append(f"    Location: {table_info['storage_location']}")

                # Add columns
                columns = table_info.get("columns", [])
                for column in columns:
                    nullable_str = (
                        "NULL" if column.get("nullable", True) else "NOT NULL"
                    )
                    col_type = column.get(
                        "type_text", column.get("type_name", "UNKNOWN")
                    )
                    result.append(
                        f"    Column: {column['name']} {col_type} {nullable_str}"
                    )
                    if column.get("comment"):
                        result.append(f"      Comment: {column['comment']}")

        return "\n".join(result) if result else "No existing schemas or tables found"

    def _extract_changes_list(self, changes_needed: str) -> List[str]:
        """Extract list of changes from the changes_needed string."""
        changes = []
        lines = changes_needed.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):  # Skip empty lines and comments
                # Clean up common list prefixes
                for prefix in ["- ", "* ", "• ", "1. ", "2. ", "3. ", "4. ", "5. "]:
                    if line.startswith(prefix):
                        line = line[len(prefix) :].strip()
                        break
                if line:
                    changes.append(line)

        return (
            changes
            if changes
            else ["Schema changes needed (see SQL script for details)"]
        )
