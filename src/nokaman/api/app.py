from __future__ import annotations

from nokaman import __version__
from nokaman.eval.adaptive import adaptive_session
from nokaman.eval.metrics import placement_test
from nokaman.eval.pipeline import evaluate_demo, evaluate_text
from nokaman.rubrics.registry import SUPPORTED_LANGUAGES, get_language_meta

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise ImportError("Install nokaman[api] for FastAPI support") from exc

app = FastAPI(title="NokaMan", version=__version__)

DEV_WEB_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_WEB_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["content-type"],
)


class TextReq(BaseModel):
    language: str = "en"
    text: str = Field(..., min_length=1)
    skill: str = "writing"


class PlacementReq(BaseModel):
    language: str = "en"
    answers: list[str] = Field(..., min_length=1)


class AdaptiveReq(BaseModel):
    language: str = "en"
    answers: list[str] = Field(default_factory=list)
    administered_ids: list[str] = Field(default_factory=list)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "nokaman",
        "version": __version__,
        "languages": sorted(SUPPORTED_LANGUAGES),
    }


@app.get("/languages")
def languages() -> dict:
    return {"languages": [get_language_meta(code) for code in sorted(SUPPORTED_LANGUAGES)]}


@app.post("/assess/text")
def assess_text(req: TextReq) -> dict:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"unsupported language {req.language}")
    return evaluate_text(req.language, req.text, skill=req.skill)


@app.post("/assess")
def assess(req: TextReq) -> dict:
    return assess_text(req)


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


@app.post("/assess/adaptive")
def assess_adaptive(req: AdaptiveReq) -> dict:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"unsupported language {req.language}")
    return adaptive_session(req.language, req.answers, administered_ids=req.administered_ids)
