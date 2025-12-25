from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_folders():
    return {"folders": []}

@router.post("/")
async def create_folder():
    return {"message": "Folder creation not yet implemented"}