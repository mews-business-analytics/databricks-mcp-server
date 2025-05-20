from typing import Optional
from mcp.server.fastmcp import FastMCP
from dbapi import execute_statement, list_databricks_views_sdk
from databricks_formatter import format_query_results


mcp = FastMCP("databricks")

@mcp.tool()
async def execute_sql_query(sql: str) -> str:
    """Execute a SQL query on Databricks and return the results.
    Args:
        sql: The SQL query to execute
    """
    try:
        result = await execute_statement(sql)
        return format_query_results(result)
    except Exception as e:
        return f"Error executing SQL query: {str(e)}"


@mcp.tool()
async def list_schemas(catalog: str) -> str:
    """List all available schemas in a Databricks catalog.
    Args:
        catalog: The catalog name to list schemas from
    """
    sql = f"SHOW SCHEMAS IN {catalog}"
    try:
        result = await execute_statement(sql)
        return format_query_results(result)
    except Exception as e:
        return f"Error listing schemas: {str(e)}"


@mcp.tool()
async def list_tables(schema: str) -> str:
    """List all tables in a specific schema.
    
    Args:
        schema: The schema name to list tables from
    """
    sql = f"SHOW TABLES IN {schema}"
    try:
        result = await execute_statement(sql)
        return format_query_results(result)
    except Exception as e:
        return f"Error listing tables: {str(e)}"


@mcp.tool()
async def describe_table(table_name: str) -> str:
    """Describe a table's schema.
    
    Args:
        table_name: The fully qualified table name (e.g., schema.table_name)
    """
    sql = f"DESCRIBE TABLE {table_name}"
    try:
        result = await execute_statement(sql)
        return format_query_results(result)
    except Exception as e:
        return f"Error describing table: {str(e)}"


@mcp.tool()
async def list_views(catalog_name: str, schema_name: str) -> str:
    """List all views in a specific catalog and schema.
    Args:
        catalog_name: The catalog name.
        schema_name: The schema name.
    """
    try:
        result = await list_databricks_views_sdk(catalog_name=catalog_name, schema_name=schema_name)
        return format_query_results(result)
    except Exception as e:
        return f"Error listing views: {str(e)}"


@mcp.tool()
async def get_view_definition(view_name: str) -> str:
    """Get the SQL DDL definition for a specific view.
    Args:
        view_name: The fully qualified view name (e.g., catalog_name.schema_name.view_name)
    """
    sql = f"SHOW CREATE TABLE {view_name}"
    try:
        result = await execute_statement(sql)
        return format_query_results(result)
    except Exception as e:
        return f"Error getting view definition: {str(e)}"


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')