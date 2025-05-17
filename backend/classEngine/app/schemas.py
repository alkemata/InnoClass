from pydantic import BaseModel
from typing import List

class SearchRequest(BaseModel):
    mode: str            # “sdgs” or “targets”
    selected: List[str]
    keywords: str
    page: int = 0

class SearchHit(BaseModel):
    id: str
    title: str
    excerpt: str
    sdgs: List[str]
    targets: List[str]

class FeedbackRequest(BaseModel):
    doc_id: str
    mode: str           # “sdgs” or “targets”
    feedback: str       # “up” or “down”
