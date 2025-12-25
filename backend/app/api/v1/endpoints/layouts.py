from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_layouts():
    return {"layouts": []}

@router.post("/")
async def create_layout():
    return {"message": "Layout creation not yet implemented"}
