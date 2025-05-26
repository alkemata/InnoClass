from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
from elastic import es # Assuming elastic.py is in the same directory
from elasticsearch import NotFoundError # For specific error handling

router = APIRouter()

class CheckPageDataResponse(BaseModel):
    id: str
    title: str
    cleaned_text: str
    sdg: List[str] # This should ideally be List[SdgItem] if we want to return the full structure
    target: List[str] # Assuming target is still a list of strings
    valid: bool
    reference: bool

class PaginatedCheckPageDataResponse(BaseModel):
    entry: Optional[CheckPageDataResponse] = None
    total: int
    offset: int

@router.get("/check/entry", response_model=PaginatedCheckPageDataResponse) # Renamed route and response model
async def get_entry_by_offset( # Renamed function
    offset: int = 0, # Added offset parameter
    filter_validation: Optional[bool] = None,
    filter_reference: Optional[bool] = None
):
    query_conditions = []
    if filter_validation is not None:
        query_conditions.append({"term": {"validation": filter_validation}})
    else:
        # Default behavior: if no validation filter is specified, 
        # it implies no preference on validation status, so don't add a default term.
        # If you always want to filter by "valid: False" by default, uncomment the next line.
        # query_conditions.append({"term": {"valid": False}}) 
        pass


    if filter_reference is not None:
        query_conditions.append({"term": {"reference": filter_reference}})

    # If there are no conditions, match all documents. Otherwise, use bool must.
    if not query_conditions:
        query_dict = {"match_all": {}}
    else:
        query_dict = {"bool": {"must": query_conditions}}

    entry_data: Optional[CheckPageDataResponse] = None
    total_hits = 0

    try:
        # 1. Get total count
        print("counting")
        print(query_dict)
        count_res = await es.count(index="main_table", body={"query": query_dict})
        total_hits = count_res.get('count', 0)
        print(total_hits)
        # 2. Get the specific entry if offset is valid and total_hits > 0
        if total_hits > 0 and offset < total_hits:
            search_query_body = {
                "query": query_dict,
                "from": offset,
                "size": 1
            }
            print(search_query_body)
            res = await es.search(index="reference", body=search_query_body)
            if res["hits"]["hits"]:
                hit = res["hits"]["hits"][0]
                src = hit["_source"]
                entry_data = CheckPageDataResponse(
                    id=hit["_id"],
                    title=src.get("title", ""),
                    cleaned_text=src.get("cleaned_text", ""),
                    # Assuming sdg in ES is List of strings. If it's List of dicts, this needs adjustment
                    # or CheckPageDataResponse.sdg needs to be List[SdgItem]
                    sdg=src.get("sdg", []), 
                    target=src.get("target", []),
                    valid=src.get("valid", False),
                    reference=src.get("reference", False)
                )
        elif offset >= total_hits and total_hits > 0 : # Offset out of bounds but there are documents
             # It's a valid scenario to request an offset beyond the total hits.
             # In this case, entry_data remains None, and total_hits is reported.
             # No HTTPException 404 should be raised here.
             pass


    except Exception as e:
        print(f"Elasticsearch operation failed: {e}") # Log error
        raise HTTPException(status_code=500, detail="Elasticsearch operation failed")

    return PaginatedCheckPageDataResponse(entry=entry_data, total=total_hits, offset=offset)

class SdgItem(BaseModel):
    value: str
    score: float

class UpdateSdgRequest(BaseModel):
    doc_id: str
    sdgs: List[SdgItem] # Changed from List[str]

@router.put("/check/update_sdgs", response_model=Dict[str, str])
async def update_entry_sdgs(req: UpdateSdgRequest):
    script_body = {
        "source": "ctx._source.sdg = params.new_sdgs",
        "params": {
            # Use model_dump() for Pydantic v2+ to convert SdgItem objects to dicts
            "new_sdgs": [sdg.model_dump() for sdg in req.sdgs] 
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

class UpdateReferenceRequest(BaseModel):
    doc_id: str
    reference: bool

@router.put("/check/update_reference", response_model=Dict[str, str])
async def update_entry_reference_status(req: UpdateReferenceRequest):
    script_body = {
        "source": "ctx._source.reference = params.new_reference_status",
        "params": {
            "new_reference_status": req.reference
        }
    }
    try:
        await es.update(
            index="reference", # Assuming "reference" index as used elsewhere in the file
            id=req.doc_id,
            body={"script": script_body}
        )
        return {"status": "success", "message": "Reference status updated successfully"}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Document with id {req.doc_id} not found.")
    except Exception as e:
        # Log the error e for debugging
        # print(f"Error updating reference status for doc {req.doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating reference status.")
