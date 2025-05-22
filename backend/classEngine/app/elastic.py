from elasticsearch import AsyncElasticsearch
import os

ELASTICSEARCH_USER = os.environ.get("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
es = AsyncElasticsearch(hosts="http://elasticsearch:9200",                    basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
                    verify_certs=False, # Use with caution
                    request_timeout=60)
INDEX="main_table"
REVIEW_INDEX="fb_table"

async def update_feedback(index: str, doc_id: str, field: str):
    # increment up/down counter
    script = {
        "source": f"ctx._source.{field} += params.count",
        "lang": "painless",
        "params": {"count": 1}
    }
    await es.update(index=index, id=doc_id, body={"script": script})
    # optionally check threshold
    doc = await es.get(index=index, id=doc_id)
    return doc["_source"]
