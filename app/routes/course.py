import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, status

from app.deps import require_api_key

router = APIRouter(prefix="/course", tags=["course"], dependencies=[Depends(require_api_key)])

_SEED_PATH = Path(__file__).parents[2] / "seed.json"


def _load() -> dict:
    try:
        with open(_SEED_PATH, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"title": "Unavailable", "status": 503, "detail": "seed.json not found."},
        )


@router.get("")
def get_course() -> dict:
    data = _load()
    return {
        "course": data.get("course", {}),
        "gap_analysis": data.get("gap_analysis", {}),
    }
