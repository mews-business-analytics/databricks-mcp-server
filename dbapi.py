from typing import Any, Dict, Optional, List
import os
import asyncio
import httpx
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import TableType

# Load environment variables from .env file
load_dotenv()

# Configuration constants
DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
DATABRICKS_SQL_WAREHOUSE_ID = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID", "")

w = WorkspaceClient()

# API endpoints
STATEMENTS_API = "/api/2.0/sql/statements"
STATEMENT_API = "/api/2.0/sql/statements/{statement_id}"


async def make_databricks_request(
    method: str,
    endpoint: str,
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a request to the Databricks API with proper error handling."""
    url = f"{DATABRICKS_HOST}{endpoint}"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            if method.lower() == "get":
                response = await client.get(url, headers=headers, params=params, timeout=30.0)
            elif method.lower() == "post":
                response = await client.post(url, headers=headers, json=json_data, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_message += f" - {error_detail.get('message', '')}"
            except Exception:
                pass
            raise Exception(error_message)
        except Exception as e:
            raise Exception(f"Error making request to Databricks API: {str(e)}")


async def execute_statement(sql: str, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute a SQL statement and wait for its completion."""
    if not warehouse_id:
        warehouse_id = DATABRICKS_SQL_WAREHOUSE_ID
    
    if not warehouse_id:
        raise ValueError("Warehouse ID is required. Set DATABRICKS_SQL_WAREHOUSE_ID environment variable or provide it as a parameter.")
    
    # Create the statement
    statement_data = {
        "statement": sql,
        "warehouse_id": warehouse_id,
        "wait_timeout": "0s"  # Don't wait for completion in the initial request
    }
    
    response = await make_databricks_request("post", STATEMENTS_API, json_data=statement_data)
    statement_id = response.get("statement_id")
    
    if not statement_id:
        raise Exception("Failed to get statement ID from response")
    
    # Poll for statement completion
    max_retries = 60  # Maximum number of retries (10 minutes with 10-second intervals)
    retry_count = 0
    
    while retry_count < max_retries:
        statement_status = await make_databricks_request(
            "get", 
            STATEMENT_API.format(statement_id=statement_id)
        )
        
        status = statement_status.get("status", {}).get("state")
        
        if status == "SUCCEEDED":
            return statement_status
        elif status in ["FAILED", "CANCELED"]:
            error_message = statement_status.get("status", {}).get("error", {}).get("message", "Unknown error")
            raise Exception(f"Statement execution failed: {error_message}")
        
        # Wait before polling again
        await asyncio.sleep(10)
        retry_count += 1
    
    raise Exception("Statement execution timed out")


async def list_databricks_views_sdk(catalog_name: str, schema_name: str) -> Dict[str, Any]:
    """List views in a schema using Databricks SDK and format for query_formatter."""
    views_data = []
    try:
        # Iterate over TableInfo objects returned by w.tables.list
        all_tables_and_views = w.tables.list(catalog_name=catalog_name, schema_name=schema_name)
        for item in all_tables_and_views:
            if item.table_type == TableType.VIEW:
                views_data.append([
                    item.name if item.name else "",
                    item.catalog_name if item.catalog_name else "",
                    item.schema_name if item.schema_name else "",
                    str(item.table_type.value) if item.table_type else "", 
                    item.comment if item.comment else ""
                ])
    except Exception as e:
        return {
            "manifest": {"schema": {"columns": [{"name": "Error"}]}},
            "result": {"data_array": [[f"Error listing views from SDK: {str(e)}"]]}
        }

    column_schema = [
        {"name": "Name"},
        {"name": "Catalog"},
        {"name": "Schema"},
        {"name": "Type"},
        {"name": "Comment"}
    ]
    
    if not views_data: # Handle case where no views are found
        return {
            "manifest": {"schema": {"columns": column_schema}},
            "result": {"data_array": []} # Pass empty list not None
        }

    return {
        "manifest": {"schema": {"columns": column_schema}},
        "result": {"data_array": views_data}
    } 