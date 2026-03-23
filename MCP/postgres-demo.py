import psycopg2
import json
import orjson
from loguru import logger
from mcp.server.fastmcp import FastMCP
from datetime import datetime
from decimal import Decimal

#create MCP server
mcp = FastMCP("Postgres_Demo")

@mcp.tool()
def query_data(sql_query: str) -> str:
    """ Execute Postgres SQL queries safely for all the tables        
        Understand the data types of the relevant columns for the query and
        frame the final query appropriately.
        If execution fails, introspect the query and do necessary corrections
        for correct response
    """

    logger.info(f"Executing SQL query: {sql_query}")
   
    DB_NAME="" # provide DB_NAME
    DB_HOST="" # provide DB_HOST
    DB_USER="" # provide DB_USER
    DB_PASS="" # provide DB_PASS
    DB_PORT="5432" # provide DB_PORT

    # ------- Connection & Exceution -----------
    conn = None
    cursor = None

    try:
        # 1. Establish the connection
        logger.info(f"Connecting to DB: {DB_NAME}")
        conn = psycopg2.connect(
            dbname = DB_NAME,
            user = DB_USER,
            password = DB_PASS,
            host = DB_HOST,
            port = DB_PORT
        )

        logger.info("Connection Established..")

        # 2. Create a cursor object which allows you to execute SQL comments
        cursor = conn.cursor()

        # 3. Execute the SQL query
        logger.info(f"\n Executing Query: {sql_query}")
        cursor.execute(sql_query)

        # 4. Fetch the results
        rows = cursor.fetchall()
    finally:
        # 5. Close the cursor and connection
        if cursor is not None:
            cursor.close()
            logger.info("Cursor closed...")
        if conn is not None:
            conn.close()
            logger.info("Connection closed...")

    logger.info("\n Script Execution finsihed...")
    #return json.dumps(rows, indent=2, default=default_serializer)
    return orjson.dumps(rows, default=default_serializer)

def default_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def test_query()-> str:
    logger.info("---Executing Query---")
    test_query = "SELECT * FROM <table_name>;" # Provide table, schema names etc.
    result = query_data(test_query)
    logger.info(f"Final Result: {result}")

if __name__ == "__main__":
    logger.info("Starting Server")
    # Initialize and run the server
    mcp.run(transport="stdio")
    #test_query()

