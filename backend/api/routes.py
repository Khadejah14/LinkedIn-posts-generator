import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent.parent))

from services.post_service import optimize_post, batch_optimize
from services.analysis_service import (
    analyze_voice,
    get_available_creators,
    compare_with_multiple_creators,
)

router = APIRouter()


class OptimizeRequest(BaseModel):
    draft: str
    past_posts: list[str] | None = None
    score_hook: bool = False


class BatchOptimizeRequest(BaseModel):
    drafts: list[str]
    past_posts: list[str] | None = None
    score_hooks: bool = False


class AnalyzeRequest(BaseModel):
    past_posts: list[str]
    creator_name: str | None = None


class MultiCreatorRequest(BaseModel):
    past_posts: list[str]
    creator_names: list[str] | None = None


@router.post("/optimize")
def optimize_endpoint(req: OptimizeRequest):
    try:
        return optimize_post(req.draft, req.past_posts, req.score_hook)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize/batch")
def batch_optimize_endpoint(req: BatchOptimizeRequest):
    try:
        return batch_optimize(req.drafts, req.past_posts, req.score_hooks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
def analyze_endpoint(req: AnalyzeRequest):
    try:
        return analyze_voice(req.past_posts, req.creator_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/multi-creator")
def multi_creator_endpoint(req: MultiCreatorRequest):
    try:
        return compare_with_multiple_creators(req.past_posts, req.creator_names)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/creators")
def get_creators():
    return {"creators": get_available_creators()}
