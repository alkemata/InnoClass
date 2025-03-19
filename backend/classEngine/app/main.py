from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch, ElasticsearchException

app = FastAPI()

# Root endpoint returns a simple testing string.
@app.get("/")
def read_root():
    return "testing"

# /status endpoint returns Elasticsearch cluster health.
@app.get("/status")
def get_status():
    try:
        # Create an Elasticsearch client instance.
        es = Elasticsearch("http://localhost:9200")
        
        # Retrieve the cluster health information.
        health = es.cluster.health()
        return health
    except ElasticsearchException as e:
        # If there's an error connecting to Elasticsearch or retrieving health data,
        # raise an HTTP 500 error with a message.
        raise HTTPException(status_code=500, detail=f"Error connecting to Elasticsearch: {e}")

# To run this FastAPI app, use:
# uvicorn your_filename:app --reload
