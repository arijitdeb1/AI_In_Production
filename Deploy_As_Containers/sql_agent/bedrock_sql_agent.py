from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from langchain_aws import ChatBedrock
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
import os
import uuid
from loguru import logger
from dotenv import load_dotenv
import subprocess
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sqlalchemy import create_engine

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Bedrock SQL Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open to all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
# Initialize the Bedrock model

model = ChatBedrock(
    model_id="arn:aws:bedrock:us-east-1:<ACCOUNT-ID>:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0", ## Replace ACCOUNT-ID
    provider="anthropic",
    region_name="us-east-1",
    model_kwargs={
            "max_tokens": 4000,
            "temperature": 0.7,
        }
)

DB_URI = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','5432')}/{os.getenv('DB_NAME')}"
    f"?sslmode={os.getenv('DB_SSLMODE')}&sslrootcert={os.getenv('DB_SSLROOTCERT')}"
)

# Initialize the SQL Database connection
db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','5432')}/{os.getenv('DB_NAME')}?sslmode={os.getenv('DB_SSLMODE')}&sslrootcert={os.getenv('DB_SSLROOTCERT')}"
)

# Log database details
logger.info(f"Dialect: {db.dialect}")
logger.info(f"Available tables: {db.get_usable_table_names()}")

# Initialize the SQL Database Toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()

# Log available tools
for tool in tools:
    logger.info(f"{tool.name}: {tool.description}")

# Define the system prompt
system_prompt = """
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run,
then look at the results of the query and return the answer. Unless the user
specifies a specific number of examples they wish to obtain, always limit your
query to at most {top_k} results.

You can order the results by a relevant column to return the most interesting
examples in the database. Never query for all the columns from a specific table,
only ask for the relevant columns given the question.

You MUST double check your query before executing it. If you get an error while
executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
database.

To start you should ALWAYS look at the tables in the database to see what you
can query. Do NOT skip this step.

Then you should query the schema of the most relevant tables.
""".format(
    dialect=db.dialect,
    top_k=5,
)

# Create the agent
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    middleware=[ 
        HumanInTheLoopMiddleware( 
            interrupt_on={"sql_db_query": True}, 
            description_prefix="Tool execution pending approval", 
        ), 
    ], 
    checkpointer=InMemorySaver(),
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    thread_id: str

class QueryResponse(BaseModel):
    response: str
    thread_id: str

@app.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """
    Endpoint to query the SQL database using the agent.

    - **question**: The user's question to query the database.
    - **thread_id**: The thread ID for the conversation.
    """
    logger.info(f"Received query request: question='{request.question}', thread_id='{request.thread_id}'")
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        response_text = ""

        # Check if this is a follow-up request with a decision
        if request.question.lower() in ["yes", "no"]:
            decision_type = "approve" if request.question.lower() == "yes" else "reject"
            logger.info(f"User decision received: {decision_type}")

            # Resume the agent with the user's decision
            for step in agent.stream(
                Command(resume={"decisions": [{"type": decision_type, "message": "User decision processed."}]}),
                config,
                stream_mode="values",
            ):
                if "messages" in step:
                    message = step["messages"][-1]
                    if message.type == "ai":
                        response_text = message.content
                        logger.info("Agent response received after user decision.")

            if not response_text:
                logger.error("No response from agent after user decision.")
                # Reframe the query and ask the user for confirmation
                return QueryResponse(
                    response="The agent failed to respond. Would you like to reframe the query or try again?",
                    thread_id=request.thread_id,
                )

            return QueryResponse(response=response_text, thread_id=request.thread_id)

        # Initial request handling
        logger.info("Starting agent query execution...")
        for step in agent.stream(
            {"messages": [{"role": "user", "content": request.question}]},
            config,
            stream_mode="values",
        ):
            logger.debug(f"Agent step: {step}")
            if "__interrupt__" in step:
                logger.info("Interrupt detected. Responding with approval prompt...")
                interrupt = step["__interrupt__"][0]
                for action_request in interrupt.value["action_requests"]:
                    sql_query = action_request.get("args", {}).get("query", "SQL query not provided")
                    logger.info(f"SQL Query: {sql_query}")

                    # Print current checkpointer contents
                    #current_state = agent.checkpointer.get()
                    #logger.info(f"Current checkpointer contents: {current_state}")

                    # Store the interrupt state in memory (checkpointer)
                    '''
                    agent.checkpointer.save(
                        thread_id=request.thread_id,
                        state={"interrupt": interrupt, "sql_query": sql_query},
                    )
                    '''
                    
                    # Respond with the approval prompt
                    return QueryResponse(
                        response=f"Do you approve to execute the below query?\n\n**{sql_query}**",
                        thread_id=request.thread_id,
                    )

            elif "messages" in step:
                message = step["messages"][-1]
                logger.debug(f"Message type: {message.type}, Content: {message.content}")
                if message.type == "ai":
                    response_text = message.content  # Replace content to capture only the last response
                    logger.info("Agent response received.")

        if not response_text:
            logger.error("No response from agent within the expected time.")
            return QueryResponse(
                response="The agent did not respond within the expected time. Please try again later or contact support.",
                thread_id=request.thread_id,
            )

        logger.info(f"Query execution successful: response='{response_text}'")
        return QueryResponse(response=response_text, thread_id=request.thread_id)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "timestamp": str(uuid.uuid4())}


@app.get("/debug-dns")
def debug_dns():
    try:
        # Runs the standard 'getent' command to resolve the host
        result = subprocess.check_output(
            ["getent", "hosts", "bedrock-runtime.us-east-1.amazonaws.com"], 
            stderr=subprocess.STDOUT
        ).decode()
        return {"status": "success", "resolved_ip": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@app.post("/create_table")
async def create_table_from_excel(table_name: str):
    """
    Reads an Excel file defined in ENV and creates a table in RDS.
    """
    # Get the file path from an environment variable
    file_path = os.getenv("EXCEL_FILE_PATH", "data.xlsx")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File {file_path} not found in container.")

    try:
        # Read the Excel file into a Pandas DataFrame
        df = pd.read_excel(file_path)

        # Create a standard SQLAlchemy engine to handle the data transfer
        engine = create_engine(DB_URI)

        # Upload the data: 
        # 'replace' will drop the table if it exists and recreate it.
        # 'append' will add to an existing table.
        df.to_sql(table_name, engine, index=False, if_exists='replace')

        return {
            "message": f"Table '{table_name}' created successfully",
            "rows_imported": len(df),
            "file_used": file_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("bedrock_sql_agent:app", host="0.0.0.0", port=8000, reload=True)
