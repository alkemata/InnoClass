import logging
logging.basicConfig(level=logging.INFO)
logging.info("FastAPI app starting")
from fastapi import FastAPI, HTTPException, Depends
from elasticsearch import Elasticsearch, helpers
import elasticsearch
print(f"Elasticsearch version: {elasticsearch.__version__}")
from elasticsearch.exceptions import ConnectionError, RequestError, NotFoundError, AuthenticationException
from typing import Optional
import os
from dotenv import load_dotenv
import json
import re
import string
from tqdm import tqdm  # Optional: for progress bars
from sentence_transformers import SentenceTransformer

load_dotenv()  # Load environment variables from .env

app = FastAPI()

# Configuration from environment variables
ELASTICSEARCH_URL = "http://elasticsearch:9200" #Default added incase no .env
ELASTICSEARCH_USER = os.environ.get("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
logging.info('NAME: '+ELASTICSEARCH_USER)
logging.info(ELASTICSEARCH_PASSWORD)
# Dependency Injection for Elasticsearch client
def get_elasticsearch_client() -> Elasticsearch:

    try:
        es = Elasticsearch(
            ELASTICSEARCH_URL,
            basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
            verify_certs=False, # Use with caution
        )
        yield es
    except (ConnectionError, AuthenticationException) as e:
        raise HTTPException(status_code=500, detail=f"Error initializing Elasticsearch client: {e}")
    finally:
        if 'es' in locals():
            es.close()

# Root endpoint returns a simple testing string.
@app.get("/")
def read_root():
    return "testing"

# /status endpoint returns Elasticsearch cluster health.
@app.get("/status")
def get_status(es: Elasticsearch = Depends(get_elasticsearch_client)):
    try:
        health = es.cluster.health()
        return health
    except (ConnectionError, RequestError) as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Elasticsearch cluster health: {e}")

#Example of a search endpoint.
@app.get("/search/{index}")
def search_index(index: str, query: Optional[str] = None, es: Elasticsearch = Depends(get_elasticsearch_client)):
    try:
        if query:
            results = es.search(index=index, query={"match": {"_all": query}})
        else:
            results = es.search(index=index)
        return results
    except (ConnectionError, RequestError, NotFoundError) as e:
        raise HTTPException(status_code=500, detail=f"Error searching Elasticsearch index '{index}': {e}")
    
# /status endpoint returns Elasticsearch cluster health.
@app.get("/test")
def get_test():
# --- Configuration ---
    try:
        es_client = Elasticsearch(
            ELASTICSEARCH_HOSTS,
                basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
                verify_certs=False, # Use with caution
            #request_timeout=60
        )
        # Test connection
        if not es_client.ping():
            raise ValueError("Connection to Elasticsearch failed!")
        print("Successfully connected to Elasticsearch.")
        health = es_client.cluster.health()
        return "Health:"+str(health)
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        exit()
