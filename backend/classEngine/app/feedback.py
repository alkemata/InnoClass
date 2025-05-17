from fastapi import APIRouter, HTTPException
from app.schemas import FeedbackRequest
from app.elastic import update_feedback

router = APIRouter()

UP_THRESHOLD = 5
INDEX_NAME = "documents"
FIELD_MAP = {"up": "up_votes", "down": "down_votes"}

@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    if req.feedback not in FIELD_MAP:
        raise HTTPException(400, "Invalid feedback")
    src = await update_feedback(
        INDEX_NAME, req.doc_id, FIELD_MAP[req.feedback]
    )
    # if up_votes ≥ threshold, you could add to a review index or write to file
    if FIELD_MAP["up"] in src and src[FIELD_MAP["up"]] >= UP_THRESHOLD:
        # e.g. await es.index(index="to_review", id=req.doc_id, document=src)
        pass
    return {"status": "ok", "counts": {
        "up": src.get("up_votes",0),
        "down": src.get("down_votes",0)
    }}
