#!/usr/bin/env python3
"""Main CLI interface for Schemax."""

import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .change_generator import ChangeGenerator
from .config import Config
from .databricks_client import DatabricksClient
from .exceptions import SchemaxError
from .schema_parser import SchemaParser

# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config-file", type=click.Path(exists=True), help="Path to config file")
@click.pass_context
def cli(ctx, verbose: bool, config_file: Optional[str]):
    """Schemax - Databricks Schema Management CLI Tool."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = Config.load(config_file)

    if verbose:
        console.print("[green]✓[/green] Loaded configuration", style="dim")


@cli.command()
@click.option(
    "--schema-file",
    "-f",
    required=True,
    type=click.Path(exists=True),
    help="Path to YAML schema definition file",
)
@click.option("--target-catalog", required=True, help="Target catalog name")
@click.option("--target-schema", help="Target schema name (optional)")
@click.option("--dry-run", is_flag=True, help="Show changes without applying them")
@click.option("--output", "-o", type=click.Path(), help="Output change script to file")
@click.pass_context
def generate(
    ctx,
    schema_file: str,
    target_catalog: str,
    target_schema: Optional[str],
    dry_run: bool,
    output: Optional[str],
):
    """Generate change script by comparing schema definition with target environment."""
    try:
        config = ctx.obj["config"]
        verbose = ctx.obj["verbose"]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:

            # Parse schema definition
            task1 = progress.add_task("Parsing schema definition...", total=None)
            parser = SchemaParser()
            schema_def = parser.parse_file(schema_file)
            progress.update(task1, description="✓ Parsed schema definition")

            if verbose:
                console.print(
                    f"[dim]Found {len(schema_def.schemas)} "
                    f"schema(s) in definition[/dim]"
                )

            # Connect to Databricks
            task2 = progress.add_task("Connecting to Databricks...", total=None)
            databricks_client = DatabricksClient(config)
            progress.update(task2, description="✓ Connected to Databricks")

            # Inspect target environment
            task3 = progress.add_task("Inspecting target environment...", total=None)
            current_state = databricks_client.get_current_state(
                target_catalog, target_schema
            )
            progress.update(task3, description="✓ Inspected target environment")

            # Generate change script
            task4 = progress.add_task("Generating change script...", total=None)
            change_generator = ChangeGenerator(config, databricks_client)
            change_script = change_generator.generate_changes(schema_def, current_state)
            progress.update(task4, description="✓ Generated change script")

        # Display results
        if change_script.has_changes():
            console.print("\n")
            console.print(
                Panel(
                    f"[bold green]Changes Required[/bold green]\n\n{change_script.summary()}",
                    title="Change Summary",
                    border_style="green",
                )
            )

            if verbose or dry_run:
                console.print("\n[bold]Generated SQL Script:[/bold]")
                console.print(f"[dim]{change_script.sql}[/dim]")

            if output:
                Path(output).write_text(change_script.sql, encoding="utf-8")
                console.print(f"\n[green]✓[/green] Change script saved to {output}")

        else:
            console.print("\n")
            console.print(
                Panel(
                    "[bold green]No changes required[/bold green]\n\n"
                    "Target environment matches schema definition.",
                    title="Result",
                    border_style="green",
                )
            )

    except SchemaxError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        if verbose:
            import traceback

            console.print(traceback.format_exc(), style="dim")
        sys.exit(1)


@cli.command()
@click.option(
    "--schema-file",
    "-f",
    required=True,
    type=click.Path(exists=True),
    help="Path to YAML schema definition file",
)
@click.option("--target-catalog", required=True, help="Target catalog name")
@click.option("--target-schema", help="Target schema name (optional)")
@click.option("--auto-approve", is_flag=True, help="Apply changes without confirmation")
@click.pass_context
def apply(
    ctx,
    schema_file: str,
    target_catalog: str,
    target_schema: Optional[str],
    auto_approve: bool,
):
    """Apply schema changes to target environment."""
    try:
        # First generate the changes
        ctx.invoke(
            generate,
            schema_file=schema_file,
            target_catalog=target_catalog,
            target_schema=target_schema,
            dry_run=True,
            output=None,
        )

        # TODO: Implement apply logic
        # config = ctx.obj["config"]
        # databricks_client = DatabricksClient(config)

        if not auto_approve:
            if not click.confirm("\nDo you want to apply these changes?"):
                console.print("[yellow]Aborted.[/yellow]")
                return

        console.print("\n[red]Apply functionality not yet implemented.[/red]")
        console.print(
            "[dim]This will execute the generated SQL script "
            "against the target environment.[/dim]"
        )

    except SchemaxError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option(
    "--schema-file",
    "-f",
    required=True,
    type=click.Path(exists=True),
    help="Path to YAML schema definition file",
)
@click.pass_context
def validate(ctx, schema_file: str):
    """Validate schema definition file."""
    try:
        verbose = ctx.obj["verbose"]

        console.print("Validating schema definition...")
        parser = SchemaParser()
        schema_def = parser.parse_file(schema_file)

        console.print("[green]✓[/green] Schema definition is valid")

        if verbose:
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  Catalog: {schema_def.catalog.name}")
            console.print(f"  Schemas: {len(schema_def.schemas)}")

            total_tables = sum(len(schema.tables) for schema in schema_def.schemas)
            console.print(f"  Tables: {total_tables}")

    except SchemaxError as e:
        console.print(f"\n[red]Validation Error:[/red] {e}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
