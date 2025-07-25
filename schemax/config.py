"""Configuration management for Schemax."""

import os
from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from pydantic import BaseModel, field_validator
from .exceptions import ConfigurationError


class Config(BaseModel):
    """Configuration for Schemax."""

    # Databricks connection settings
    databricks_host: str
    databricks_token: str
    databricks_warehouse_id: Optional[str] = None

    # LLM settings
    llm_endpoint: str = "databricks-meta-llama-3-1-405b-instruct"
    llm_max_tokens: int = 4000
    llm_temperature: float = 0.1

    # DSPy settings
    dspy_max_retries: int = 3
    dspy_cache_dir: Optional[str] = None

    # Output settings
    output_format: str = "sql"  # sql, json
    include_comments: bool = True

    @field_validator("databricks_host")
    @classmethod
    def validate_host(cls, v):
        if not v:
            raise ValueError("Databricks host is required")
        if not v.startswith(("https://", "http://")):
            v = f"https://{v}"
        return v.rstrip("/")

    @field_validator("databricks_token")
    @classmethod
    def validate_token(cls, v):
        if not v:
            raise ValueError("Databricks token is required")
        return v

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "Config":
        """Load configuration from environment and optional config file."""
        config_data = {}

        # Load from config file if provided
        if config_file:
            try:
                with open(config_file, "r") as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config_data.update(file_config)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load config file {config_file}: {e}"
                )

        # Override with environment variables
        env_mapping = {
            "DATABRICKS_HOST": "databricks_host",
            "DATABRICKS_TOKEN": "databricks_token",
            "DATABRICKS_WAREHOUSE_ID": "databricks_warehouse_id",
            "DATABRICKS_LLM_ENDPOINT": "llm_endpoint",
            "SCHEMAX_LLM_MAX_TOKENS": "llm_max_tokens",
            "SCHEMAX_LLM_TEMPERATURE": "llm_temperature",
            "SCHEMAX_DSPY_MAX_RETRIES": "dspy_max_retries",
            "SCHEMAX_DSPY_CACHE_DIR": "dspy_cache_dir",
            "SCHEMAX_OUTPUT_FORMAT": "output_format",
            "SCHEMAX_INCLUDE_COMMENTS": "include_comments",
        }

        for env_var, config_key in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Handle type conversion
                if config_key in ["llm_max_tokens", "dspy_max_retries"]:
                    config_data[config_key] = int(env_value)
                elif config_key == "llm_temperature":
                    config_data[config_key] = float(env_value)
                elif config_key == "include_comments":
                    config_data[config_key] = env_value.lower() in ("true", "1", "yes")
                else:
                    config_data[config_key] = env_value

        try:
            return cls(**config_data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()

    def save(self, filepath: str):
        """Save configuration to file."""
        config_dict = self.to_dict()
        # Remove sensitive information
        config_dict.pop("databricks_token", None)

        try:
            with open(filepath, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        except Exception as e:
            raise ConfigurationError(f"Failed to save config file {filepath}: {e}")
