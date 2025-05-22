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
    # Build your query
    must_clauses = []

    # Add the "sdg" terms query (one of the selected in the sdg field)
    if selected_sdg:
        must_clauses.append({"terms": {"sdg": selected_sdg}})

    # Add the "keywords" query to "title" if keywords is not empty or not ""
    if keywords:
        must_clauses.append({"match": {"title": keywords}})

    # If no clauses are present, it means no specific search criteria are provided,
    # so we might want to return all documents or handle it differently.
    # For now, let's assume at least one criteria (selected_sdg or keywords) will be provided.
    if not must_clauses:
        raise HTTPException(status_code=400, detail="At least 'selected_sdg' or 'keywords' must be provided.")

    body = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        },
        "from": page * size,
        "size": size
    }

    try:
        resp = await es.search(
            index=index,
            body=body
        )
        return resp.body
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
