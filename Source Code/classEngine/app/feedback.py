from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from elastic import es, INDEX, REVIEW_INDEX # Assuming 'elastic' module provides 'es' client and index names

THRESHOLD = 5

router = APIRouter()

class Feedback(BaseModel):
    id: str  # This will be used as the document ID in Elasticsearch
    feedback: str  # "up" or "down"

@router.post("/feedback")
async def feedback(fb: Feedback):
    if fb.feedback not in ("up", "down"):
        raise HTTPException(400, "feedback must be 'up' or 'down'")

    # Determine which field to increment
    field_to_increment = f"thumbs{fb.feedback}"

    # Script to increment the counter and set 'reference' if threshold is met
    script_source = f"""
        ctx._source.{field_to_increment} += 1;
        if (ctx._source.{field_to_increment} > params.threshold) {{
            ctx._source.reference = true;
        }}
    """
    script = {
        "source": script_source,
        "lang": "painless",
        "params": {
            "threshold": THRESHOLD
        }
    }

    try:
        # Increment counter and potentially set 'reference'
        await es.update(
            index=INDEX,
            id=fb.id,  # Use fb.id as the document ID
            body={"script": script},
            # If the document doesn't exist, create it with initial values
            upsert={
                "thumbsup": 0,
                "thumbsdown": 0,
                "reference": False,
                field_to_increment: 1 # Initialize the specific field that triggered the upsert
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to update document: {e}")

    # Fetch the updated document to return the new count and reference status
    try:
        doc = await es.get(index=INDEX, id=fb.id)
        current_count = doc["_source"].get(field_to_increment, 0)
        is_referenced = doc["_source"].get("reference", False)
    except Exception as e:
        raise HTTPException(500, f"Failed to retrieve updated document: {e}")

    # The original request had logic to copy to REVIEW_INDEX.
    # The new requirement is to set 'reference' field in the original index.
    # If the REVIEW_INDEX logic is still desired *in addition* to setting 'reference',
    # you would keep that part here, but it's not explicitly requested for the modification.
    # For now, I'm omitting the REVIEW_INDEX logic as the new requirement is to set 'reference'.

    return {"status": "ok", "new_count": current_count, "reference": is_referenced}