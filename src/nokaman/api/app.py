from __future__ import annotations

from nokaman import __version__
from nokaman.eval.metrics import placement_test
from nokaman.eval.pipeline import evaluate_demo, evaluate_text
from nokaman.rubrics.registry import SUPPORTED_LANGUAGES

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise ImportError("Install nokaman[api] for FastAPI support") from exc

app = FastAPI(title="NokaMan", version=__version__)


class TextReq(BaseModel):
    language: str = "en"
    text: str = Field(..., min_length=1)
    skill: str = "writing"


class PlacementReq(BaseModel):
    language: str = "en"
    answers: list[str] = Field(..., min_length=1)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "nokaman",
        "version": __version__,
        "languages": sorted(SUPPORTED_LANGUAGES),
    }


@app.post("/assess/text")
def assess_text(req: TextReq) -> dict:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"unsupported language {req.language}")
    return evaluate_text(req.language, req.text, skill=req.skill)


@app.get("/assess/demo/{lang}")
def assess_demo(lang: str) -> dict:
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"unsupported language {lang}")
    return evaluate_demo(lang)


@app.post("/assess/placement")
def assess_placement(req: PlacementReq) -> dict:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"unsupported language {req.language}")
    return placement_test(req.language, req.answers)
