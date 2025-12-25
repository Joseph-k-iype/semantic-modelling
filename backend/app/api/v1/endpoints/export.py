from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def export_model():
    return {"message": "Export not yet implemented"}