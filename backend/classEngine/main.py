from fastapi import FastAPI, HTTPException, Depends
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError
from typing import Optional

app = FastAPI()

# Configuration (consider using environment variables for production)
ELASTICSEARCH_URL = "https://elasticsearch:9200"

# Dependency Injection for Elasticsearch client
def get_elasticsearch_client() -> Elasticsearch:
    try:
        es = Elasticsearch(ELASTICSEARCH_URL,verify_certs=False)
        yield es
    except ConnectionError as e:
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