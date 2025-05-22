from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from elastic import es, INDEX, REVIEW_INDEX

THRESHOLD = 5

router = APIRouter()

class Feedback(BaseModel):
    id: str
    feedback: str   # "up" or "down"

@router.post("/feedback")
async def feedback(fb: Feedback):
    if fb.feedback not in ("up","down"):
        raise HTTPException(400, "feedback must be 'up' or 'down'")
    script = {
        "source": f"ctx._source.{fb.feedback} += 1"
    }
    # increment counter
    await es.update(index=INDEX, id=fb.doc_id, body={"script": script})
    # fetch updated
    doc = await es.get(index=INDEX, id=fb.doc_id)
    cnt = doc["_source"].get(fb.feedback, 0)
    # if up reached threshold, copy to review index
    if fb.feedback=="up" and cnt >= THRESHOLD:
        # reindex: add to REVIEW_INDEX
        await es.index(index=REVIEW_INDEX, id=fb.doc_id, document=doc["_source"])
    return {"status":"ok","new_count":cnt}
