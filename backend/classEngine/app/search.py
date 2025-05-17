from fastapi import APIRouter, HTTPException
from app.schemas import SearchRequest, SearchHit
from app.elastic import search_docs

router = APIRouter()

INDEX_NAME = "documents"
MODE_FIELD_MAP = {"sdgs": "sdgs_list", "targets": "targets_list"}

@router.post("/search", response_model=list[SearchHit])
async def search(req: SearchRequest):
    if req.mode not in MODE_FIELD_MAP:
        raise HTTPException(400, "Invalid mode")
    hits = await search_docs(
        INDEX_NAME,
        mode_field=MODE_FIELD_MAP[req.mode],
        selected=req.selected,
        keywords=req.keywords,
        page=req.page,
    )
    results = []
    for h in hits:
        src = h["_source"]
        results.append(SearchHit(
            id=h["_id"],
            title=src["title"],
            excerpt=src.get("extracted_text","")[:200],
            sdgs=src["sdgs_list"],
            targets=src["targets_list"]
        ))
    return results
