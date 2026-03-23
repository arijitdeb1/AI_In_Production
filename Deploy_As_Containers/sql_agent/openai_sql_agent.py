
import os
from langchain_openai import ChatOpenAI
import psycopg2
from dotenv import load_dotenv
from loguru import logger
import orjson
from datetime import datetime
from decimal import Decimal
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware 
from langgraph.checkpoint.memory import InMemorySaver 
from langgraph.types import Command 

load_dotenv()  ## provide OPENAI_API_KEY & DB Credentials in .env file

model = ChatOpenAI(model="gpt-4.1")

db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','5432')}/{os.getenv('DB_NAME')}"
)

print(f"Dialect: {db.dialect}")
print(f"Available tables: {db.get_usable_table_names()}")
#print(f'Sample output: {db.run("SELECT * FROM projects;")}')

toolkit = SQLDatabaseToolkit(db=db, llm=model)

tools = toolkit.get_tools()

for tool in tools:
    print(f"{tool.name}: {tool.description}\n")


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

if __name__ == "__main__":
    question = "what products have been ordered by Jane Smith?"
    config = {"configurable": {"thread_id": "user1"}} 
    
    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        config, 
        stream_mode="values",
    ):
        if "__interrupt__" in step: 
            print("INTERRUPTED:") 
            interrupt = step["__interrupt__"][0] 
            for request in interrupt.value["action_requests"]: 
             print(request["description"]) 
        elif "messages" in step:
            step["messages"][-1].pretty_print()
        else:
            pass
    
    ## Provide Human Feedback to continue
    logger.info("------- Waiting for human approval...")
    
    # Get user input for approval
    while True:
        user_decision = input("\nDo you approve this action? (yes/no): ").strip().lower()
        if user_decision in ['yes', 'y', 'approve']:
            decision_type = "approve"
            break
        elif user_decision in ['no', 'n', 'reject']:
            decision_type = "reject"
            break
        else:
            print("Please enter 'yes' or 'no'")

    for step in agent.stream(
    Command(resume={"decisions": [{"type": decision_type, "message": "No, this is wrong because ..., instead do this ...",}]}), 
    config,
    stream_mode="values",
    ):
        if "messages" in step:
            step["messages"][-1].pretty_print()
        elif "__interrupt__" in step:
            print("INTERRUPTED:")
            interrupt = step["__interrupt__"][0]
            for request in interrupt.value["action_requests"]:
                print(request["description"])
        else:
            pass
