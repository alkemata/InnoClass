from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
from .elastic import es # Assuming elastic.py is in the same directory
from elasticsearch import NotFoundError # For specific error handling

router = APIRouter()

class SdgItem(BaseModel):
    value: str
    score: int

class CheckPageDataResponse(BaseModel):
    id: str
    title: str
    cleaned_text: str
    sdg: List[SdgItem]
    target: List[str]
    valid: bool
    reference: bool

@router.get("/check/next_entry", response_model=CheckPageDataResponse)
async def get_next_unvalidated_entry():
    query_body = {
        "query": {
            "term": {
                "valid": False
            }
        },
        "size": 1
    }
    try:
        res = await es.search(index="reference", body=query_body)
    except Exception as e:
        # Log the error e for debugging
        # print(f"Elasticsearch query failed: {e}")
        raise HTTPException(status_code=500, detail="Elasticsearch query failed")

    if res["hits"]["hits"]:
        hit = res["hits"]["hits"][0]
        src = hit["_source"]
 # Process sdg field to be List[SdgItem]
        sdg_data = src.get("sdg", [])
        sdg_items = [SdgItem(**item) for item in sdg_data if isinstance(item, dict)]

        return CheckPageDataResponse(
            id=hit["_id"],
            title=src.get("title", ""),
            cleaned_text=src.get("cleaned_text", ""),
            sdg=sdg_items,
            target=src.get("target", []),
            valid=src.get("valid", False),
            reference=src.get("reference", False) # Added reference field
        )
    else:
        raise HTTPException(status_code=404, detail="No unvalidated entries found.")


class UpdateSdgRequest(BaseModel):
    doc_id: str
    sdgs: List[str]

@router.put("/check/update_sdgs", response_model=Dict[str, str])
async def update_entry_sdgs(req: UpdateSdgRequest):
    script_body = {
        "source": "ctx._source.sdg = params.new_sdgs",
        "params": {
            "new_sdgs": req.sdgs
        }
    }
    try:
        await es.update(
            index="reference",
            id=req.doc_id,
            body={"script": script_body}
        )
        return {"status": "success", "message": "SDGs updated successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Document with id {req.doc_id} not found.")
    except Exception as e:
        # Log the error e for debugging
        # print(f"Error updating SDGs for doc {req.doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating SDGs.")

class UpdateValidationRequest(BaseModel):
    doc_id: str
    valid: bool

@router.put("/check/update_validation", response_model=Dict[str, str])
async def update_entry_validation_status(req: UpdateValidationRequest):
    script_body = {
        "source": "ctx._source.valid = params.new_valid_status",
        "params": {
            "new_valid_status": req.valid
        }
    }
    try:
        await es.update(
            index="reference",
            id=req.doc_id,
            body={"script": script_body}
        )
        return {"status": "success", "message": "Validation status updated successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Document with id {req.doc_id} not found.")
    except Exception as e:
        # Log the error e for debugging
        # print(f"Error updating validation status for doc {req.doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating validation status.")
