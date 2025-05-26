from fastapi import APIRouter, Query
from typing import List, Optional
from elastic import es, INDEX
from pydantic import BaseModel

router = APIRouter()

class SearchRequest(BaseModel):
    selections: List[str]
    keywords: Optional[str] = ""
    page: int = 1
    size: int = 20

class SdgItem(BaseModel):
    value: str
    score: float

class Hit(BaseModel):
    id: str
    title: str
    cleaned_text: str
    sdgs: List[SdgItem]
    targets: List[str]
    up: int
    down: int

class SearchResponse(BaseModel):
    hits: List[Hit]
    total: int

@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    print("request received!")
    # build ES bool query
    filters = []
    if req.selections:
        # Construct a terms query for 'sdgs.value' to match any of the selected SDG values
        filters.append({ "terms": { "sdg.value": req.selections}})

    filters = []
    if req.selections:
        # Use a nested query to filter on sdgs.value
        filters.append({
            "nested": {
                "path": "sdg",
                "query": {
                    "terms": {
                        "sdg.value": req.selections
                    }
                }
            }
        })
    
    must = []
    if req.keywords:
        must.append({
            "multi_match": {
                "query": req.keywords,
                "fields": ["title", "full_text"]
            }
        })
    
    body = {
        "query": {
            "bool": {
                "filter": filters,
                "must": must
            }
        },
        "sort": [
            { "sdg.score": { "order": "desc","nested": {  
                        "path": "sdg",
                    } }} 
        ],
        "from": (req.page-1)*req.size,
        "size": req.size
    }
    print(body)
    res = await es.search(index=INDEX, body=body)
    hits = []
    for h in res["hits"]["hits"]:
        src = h["_source"]
 
        hits.append(Hit(
            id=h["_id"],
            title=src["title"],
            cleaned_text=src.get("cleaned_text","")[:100],
            sdgs=[SdgItem(**sdg) for sdg in src.get("sdg",[])], # Convert to SdgItem objects
            targets=src.get("target",[]),
            up=src.get("up",0),
            down=src.get("down",0)
        ))
        print(sdgs)
    print(str(len(hits)))
    return SearchResponse(hits=hits, total=res["hits"]["total"]["value"])