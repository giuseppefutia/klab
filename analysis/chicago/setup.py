# utils/llm_setup.py
import configparser
from langchain_openai import ChatOpenAI
from database.neo4j_db import Neo4jGraphDB

def setup_llm_and_graph(config_path: str = '../../config.ini'):
    config = configparser.ConfigParser()
    config.read(config_path)

    openai_api_key = config["openai"]["api_key"]
    openai_model = config["openai"].get("model", "gpt-4.1-mini")

    llm = ChatOpenAI(
        model=openai_model,
        api_key=openai_api_key,
        temperature=0,
        max_tokens=10000,
        timeout=3000
    )

    neo4j_graph = Neo4jGraphDB()
    return llm, neo4j_graph
