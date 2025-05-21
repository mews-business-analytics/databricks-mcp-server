# Databricks MCP Server

This is a Model Context Protocol (MCP) server for executing SQL queries against Databricks using the Statement Execution API.
It can retrieve data by performing SQL requests using the Databricks API.
When used in an Agent mode, it can successfully iterate over a number of requests to perform complex tasks.
It is even better when coupled with Unity Catalog Metadata.

## Features

- Execute SQL queries on Databricks
- List available schemas in a catalog
- List tables in a schema
- Describe table schemas
- List views in a catalog and schema
- Get SQL definitions of views

## Setup

### System Requirements

- Python 3.10+
- If you plan to install via `uv`, ensure it's [installed](https://docs.astral.sh/uv/getting-started/installation/#__tabbed_1_1)

### Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/mcp-databricks-server.git
cd mcp-databricks-server
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or if using `uv`:

```bash
uv pip install -r requirements.txt
```

3. Set up your environment variables:

   Option 1: Using a .env file (recommended)
   
   Create a .env file with your Databricks credentials:
   
   ```
   DATABRICKS_HOST=your-databricks-instance.cloud.databricks.com
   DATABRICKS_TOKEN=your-databricks-access-token
   DATABRICKS_SQL_WAREHOUSE_ID=your-sql-warehouse-id
   ```

   Option 2: Setting environment variables directly
   
   ```bash
   export DATABRICKS_HOST="https://adb-5769108933149883.3.azuredatabricks.net"
   export DATABRICKS_TOKEN="your-databricks-access-token"
   export DATABRICKS_SQL_WAREHOUSE_ID="aebcaaff2f9457a3
   
You can find your SQL warehouse ID in the Databricks UI under SQL Warehouses.

### Troubleshooting Setup Issues

#### Missing Dependencies

If you encounter "ModuleNotFoundError" when starting the server, ensure all dependencies are installed:

```bash
pip install databricks-sdk httpx python-dotenv mcp asyncio
```

#### Authentication Issues

If you encounter authentication errors:
1. Verify your token has the correct permissions in Databricks
2. Ensure the host URL is correct (should include the full domain)
3. Check that your SQL warehouse ID is valid and active

#### SQL Warehouse Not Running

If queries fail to execute:
1. Ensure your SQL warehouse is running in the Databricks UI
2. The warehouse may take a few minutes to start if it was idle

## Permissions Requirements

Before using this MCP server, ensure that:

1. **SQL Warehouse Permissions**: The user associated with the provided token must have appropriate permissions to access the specified SQL warehouse. You can configure warehouse permissions in the Databricks UI under SQL Warehouses > [Your Warehouse] > Permissions.

2. **Token Permissions**: The personal access token used should have the minimum necessary permissions to perform the required operations. It is strongly recommended to:
   - Create a dedicated token specifically for this application
   - Grant read-only permissions where possible to limit security risks
   - Avoid using tokens with workspace-wide admin privileges

3. **Data Access Permissions**: The user associated with the token must have appropriate permissions to access the catalogs, schemas, and tables that will be queried.

To set SQL warehouse permissions via the Databricks REST API, you can use:
- `GET /api/2.0/sql/permissions/warehouses/{warehouse_id}` to check current permissions
- `PATCH /api/2.0/sql/permissions/warehouses/{warehouse_id}` to update permissions

For security best practices, consider regularly rotating your access tokens and auditing query history to monitor usage.

## Running the Server

### Standalone Mode

To run the server in standalone mode:

```bash
python main.py
```

This will start the MCP server using stdio transport, which can be used with Agent Composer or other MCP clients.

### Using with Cursor

To use this MCP server with [Cursor](https://cursor.sh/), you need to configure it in your Cursor settings:

1. Create a `.cursor` directory in your home directory if it doesn't already exist
2. Create or edit the `mcp.json` file in that directory:

```bash
mkdir -p ~/.cursor
touch ~/.cursor/mcp.json
```

3. Add the following configuration to the `mcp.json` file, replacing the directory path with the actual path to where you've installed this server:

```json
{
    "mcpServers": {
        "databricks": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/your/mcp-databricks-server",
                "run",
                "main.py"
            ]
        }
    }
}
```

If you're not using `uv`, you can use `python` instead:

```json
{
    "mcpServers": {
        "databricks": {
            "command": "python",
            "args": [
                "/path/to/your/mcp-databricks-server/main.py"
            ]
        }
    }
}
```

4. Restart Cursor to apply the changes

Now you can use the Databricks MCP server directly within Cursor's AI assistant.

## Available Tools

The server provides the following tools:

1. `execute_sql_query`: Execute a SQL query and return the results
   ```
   execute_sql_query(sql: str) -> str
   ```

2. `list_schemas`: List all available schemas in a specific catalog
   ```
   list_schemas(catalog: str) -> str
   ```

3. `list_tables`: List all tables in a specific schema
   ```
   list_tables(schema: str) -> str
   ```

4. `describe_table`: Describe a table's schema
   ```
   describe_table(table_name: str) -> str
   ```

5. `list_views`: List all views in a specific catalog and schema
   ```
   list_views(catalog_name: str, schema_name: str) -> str
   ```

6. `get_view_definition`: Get the SQL DDL definition for a specific view
   ```
   get_view_definition(view_name: str) -> str
   ```

## Example Usage

In Agent Composer or other MCP clients, you can use these tools like:

```
execute_sql_query("SELECT * FROM my_schema.my_table LIMIT 10")
list_schemas("my_catalog")
list_tables("my_catalog.my_schema")
describe_table("my_catalog.my_schema.my_table")
list_views("my_catalog", "my_schema")
get_view_definition("my_catalog.my_schema.my_view")
```

### Use Case: Migrating Views to dbt

This server is particularly useful for migrating views from Databricks to dbt:

1. Use `list_views` to discover all views in your catalog and schema
2. For each view, use `get_view_definition` to retrieve the SQL definition
3. Transform the SQL as needed and save it into your dbt project structure

## Handling Long-Running Queries

The server is designed to handle long-running queries by polling the Databricks API until the query completes or times out. The default timeout is 10 minutes (60 retries with 10-second intervals), which can be adjusted in the `dbapi.py` file if needed.

## Dependencies

- databricks-sdk: For interacting with the Databricks Workspace API
- httpx: For making HTTP requests to the Databricks API
- python-dotenv: For loading environment variables from .env file
- mcp: The Model Context Protocol library
- asyncio: For asynchronous operations

## Development

### Adding New Tools

If you need to add new tools:

1. Add new functions to `dbapi.py` to interact with the Databricks API
2. Register the new tools in `main.py` by adding them to the `mcp_tools` list
3. Update the documentation in this README

### Testing

To test your changes:

1. Make sure your .env file is properly configured
2. Run the server: `python main.py`
3. Try using the tools with a MCP client

