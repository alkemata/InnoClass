from fastapi import FastAPI
from app.routers import search, feedback

app = FastAPI()

origins = [
    "https://innoclass.alkemata.com",     # your frontend domain
    "https://api.innoclass.alkemata.com", # if you ever fetch against the API hostname directly
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # <-- whitelist
    allow_credentials=False,           
    allow_methods=["*"],              # GET, POST, OPTIONS, etc.
    allow_headers=["*"],              # Content-Type, X-PASSKEY, etc.
)
app.include_router(search.router)
app.include_router(feedback.router)