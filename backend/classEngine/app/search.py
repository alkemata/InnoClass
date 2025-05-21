from fastapi import APIRouter, Query
from typing import List, Optional
from app.elastic import es, INDEX
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    category: str                   # "sdgs" or "targets"
    selections: List[str]
    keywords: Optional[str] = ""
    page: int = 1
    size: int = 20

class Hit(BaseModel):
    id: str
    title: str
    extracted_text: str
    sdgs: List[str]
    targets: List[str]
    up: int
    down: int

class SearchResponse(BaseModel):
    hits: List[Hit]
    total: int

@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    # build ES bool query
    filters = [{ "terms": { req.category: req.selections }}] if req.selections else []
    must = []
    if req.keywords:
        must.append({
            "multi_match": {
                "query": req.keywords,
                "fields": ["title^2", "full_text"]
            }
        })
    body = {
        "query": {
            "bool": {
                "filter": filters,
                "must": must
            }
        },
        "from": (req.page-1)*req.size,
        "size": req.size
    }
    res = await es.search(index=INDEX, body=body)
    hits = []
    for h in res["hits"]["hits"]:
        src = h["_source"]
        hits.append(Hit(
            id=h["_id"],
            title=src["title"],
            extracted_text=src.get("extracted_text",""),
            sdgs=src.get("sdgs",[]),
            targets=src.get("targets",[]),
            up=src.get("up",0),
            down=src.get("down",0)
        ))
    return SearchResponse(hits=hits, total=res["hits"]["total"]["value"])
