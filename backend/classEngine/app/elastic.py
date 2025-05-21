from elasticsearch import AsyncElasticsearch
import os

ELASTICSEARCH_USER = os.environ.get("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.environ.get("ELASTICSEARCH_PASSWORD")
es = AsyncElasticsearch(hosts="http://elasticsearch:9200",                    basic_auth=(ELASTICSEARCH_USER, ELASTICSEARCH_PASSWORD),
                    verify_certs=False, # Use with caution
                    request_timeout=60)
INDEX="test2"
REVIEW_INDEX="test2"

async def search_docs(index: str, *,
                      mode_field: str,
                      selected: list[str],
                      keywords: str,
                      page: int = 0,
                      size: int = 20):
    # build your query
    body = {
        "query": {
            "bool": {
                "must": [
                    {"terms": {mode_field: selected}},
                    {"multi_match": {
                        "query": keywords,
                        "fields": ["title", "full_text"]
                    }}
                ]
            }
        },
        "from": page * size,
        "size": size
    }
    resp = await es.search(index=index, body=body)
    return resp["hits"]["hits"]

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
