# users.py
from fastapi import APIRouter, Depends
from auth import get_current_user, require_role

router = APIRouter()

@router.get("/profile")
def profile(user=Depends(get_current_user)):
    return {"message": f"Hello {user['sub']}!", "role": user["role"]}

@router.get("/admin")
def admin_dashboard(user=Depends(require_role("admin"))):
    return {"message": "Welcome to the admin dashboard!"}
