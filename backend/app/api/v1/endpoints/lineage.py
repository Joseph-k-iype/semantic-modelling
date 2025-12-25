from fastapi import APIRouter

router = APIRouter()

@router.get("/{entity_id}")
async def get_lineage(entity_id: str):
    return {"entity_id": entity_id, "lineage": []}